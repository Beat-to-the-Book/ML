from kafka import KafkaConsumer
import json
from app import create_app
from app.core.dependencies import db_session, redis_client
from app.models.book import Book
from app.repositories.book_repository import BookPoolRepository
from app.services.hybrid_recommender import HybridRecommender
from app.services.recommend_cache import cache_recommendations
from app.infra.kafka.kafka_producer import send_recommendations_to_kafka
from app.core.config import Config
from app.core.logger import setup_logger

logger = setup_logger()
app = create_app()

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
    recommender = HybridRecommender(book_repository)

    logger.info("[KafkaConsumer] 추천 시스템 준비 완료")

    for message in consumer:
        try:
            data = message.value if isinstance(message.value, dict) else json.loads(message.value)

            user_id = data.get('userId')
            read_books = data.get('readBooks', [])
            behavior = data.get('userBehaviors', [])

            logger.info(f"[Kafka] 수신 메시지 - userId={user_id}, 읽은 책 수={len(read_books)}, 행동 수={len(behavior)}")

            if not user_id:
                logger.warning("Kafka 메시지에 userId 없음")
                continue

            if not isinstance(read_books, list) or not isinstance(behavior, list):
                logger.warning("Kafka 메시지 형식 오류")
                continue

            recommendations = recommender.get_recommendations(read_books, behavior)

            if recommendations:
                logger.info(f"[Kafka] 추천 완료 - 추천 수={len(recommendations)}")
                cache_recommendations(user_id, {
                    "userId": user_id,
                    "recommendedBooks": recommendations
                })
                send_recommendations_to_kafka(user_id, recommendations)
            else:
                logger.warning(f"[Kafka] 추천 결과 없음 - userId={user_id}")

        except Exception as e:
            logger.error(f"[Kafka] 메시지 처리 중 예외 발생: {e}", exc_info=True)
