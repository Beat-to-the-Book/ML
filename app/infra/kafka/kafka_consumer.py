from kafka import KafkaConsumer
import json
from app import create_app
from app.core.dependencies import db_session, redis_client
from app.models.book import Book
from app.repositories.book_repository import BookPoolRepository
from app.services.model_based_recommender import ModelBasedRecommender
from app.infra.kafka.kafka_producer import send_recommendations_to_kafka
from app.infra.cache.redis_cache import set_cache
from app.core.config import Config
from app.core.logger import setup_logger
from app.utils.generate_training_dataset import append_training_row
from time import time, sleep

logger = setup_logger()
app = create_app()

def main():
    # Kafka Consumer 설정
    consumer = KafkaConsumer(
        'flask_recommendation_topic',
        bootstrap_servers=[Config.KAFKA_SERVER],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='flask-consumer-group'
    )

    # Flask 앱 컨텍스트 안에서 실행
    with app.app_context():
        # 객체 초기화
        book_repository = BookPoolRepository(db_session, Book, redis_client)
        model_recommender = ModelBasedRecommender(book_repository)

        logger.info("[KafkaConsumer] 추천 시스템 준비 완료")

        for message in consumer:
            handle(message.value, model_recommender)

def handle(message, model_recommender):
    try:
        # 메시지 값 json 파싱
        data = json.loads(message)

        user_id = data.get("userId")
        if not user_id:
            logger.warning("Kafka 메시지에 userId 없음")
            return

        read_books = data.get("readBooks", [])
        user_behaviors = data.get("userBehaviors", [])
        logger.info(f"[Kafka] 수신 - userId={user_id}, read_books={len(read_books)}, behaviors={len(user_behaviors)}")

        # 학습용 CSV 저장
        for behavior in user_behaviors:
            append_training_row(user_id, behavior, read_books)

        # 추천 연산
        start_time = time()
        recommendations = model_recommender.get_model_based_recommendations(read_books, user_behaviors)
        logger.info(f"[Kafka] 추천 연산 완료: {round(time() - start_time, 2)}초")

        # 추천 결과 캐시
        if recommendations:
            logger.info(f"[Kafka] 추천 완료 - 추천 수={len(recommendations)}")
            send_recommendations_to_kafka(user_id, recommendations)
            set_cache(redis_client, f"recommend:model:user:{user_id}", {"recommendedBooks": recommendations})
        else:
            logger.warning(f"[Kafka] 추천 결과 없음 - userId={user_id}")

        # 사용자 데이터 캐시
        context_data = {
            "readBooks": read_books,
            "userBehaviors": user_behaviors
        }

        set_cache(redis_client, f"user_context:{user_id}", context_data)

    except Exception as e:
        logger.error(f"[Kafka] 처리 중 예외 발생: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        # 컨테이너가 꺼지지 않도록 웹 서비스와 kafka consumer 분리
        while True:
            sleep(60)
