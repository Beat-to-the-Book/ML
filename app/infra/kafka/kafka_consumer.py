from kafka import KafkaConsumer
import json
from app import create_app
from app.core.dependencies import db_session, redis_client
from app.models.book import Book
from app.repositories.book_repository import BookPoolRepository
from app.services.semantic_hybrid_recommender import SemanticHybridRecommender
from app.infra.kafka.kafka_producer import send_recommendations_to_kafka
from app.core.config import Config
from app.core.logger import setup_logger
from time import time

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
        recommender = SemanticHybridRecommender(book_repository)

        logger.info("[KafkaConsumer] 추천 시스템 준비 완료")

        for message in consumer:
            handle(message.value, recommender)

def handle(message, recommender):
    try:
        # 메시지 값 json 파싱
        data = json.loads(message)

        user_id = data.get('userId')
        if not user_id:
            logger.warning("Kafka 메시지에 userId 없음");
            return

        read_books = data.get('readBooks', [])
        behavior = data.get('userBehaviors', [])
        logger.info(f"[Kafka] 수신 메시지 - userId={user_id}, 읽은 책 수={len(read_books)}, 행동 수={len(behavior)}")

        # 추천 연산
        start_time = time()
        recommendations = recommender.get_semantic_hybrid_recommendations(read_books, behavior)
        logger.info(f"[Kafka] 추천 연산 소요 시간: {round(time() - start_time, 2)}초")

        if recommendations:
            logger.info(f"[Kafka] 추천 완료 - 추천 수={len(recommendations)}")
            send_recommendations_to_kafka(user_id, recommendations)
        else:
            logger.warning(f"[Kafka] 추천 결과 없음 - userId={user_id}")

    except Exception as e:
        logger.error(f"[Kafka] 메시지 처리 중 예외 발생: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        # 컨테이너가 꺼지지 않도록 웹 서비스와 kafka consumer 분리
        while True:
            time.sleep(60)
