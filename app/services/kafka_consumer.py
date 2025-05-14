from kafka import KafkaConsumer
import json
from app import create_app, db
from app.models.book import Book
from app.services.book_pool_cache import BookPoolCache, book_pool_cache as global_cache
from app.services.recommend_service import get_combined_recommendations
from app.services.recommend_cache import cache_recommendations
from app.services.kafka_producer import send_recommendations_to_kafka
from app.config import Config
from app.logger_config import setup_logger

logger = setup_logger()
app = create_app()

# Kafka Consumer 설정
consumer = KafkaConsumer(
    'flask_recommendation_topic',
    bootstrap_servers=[Config.KAFKA_SERVER],
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest', # Kafka에 쌓여 있던 메시지를 전부 가져와서 처리 가능
    group_id='flask-consumer-group' # offset 저장하기 위한 group_id
)

# Flask 앱 컨텍스트 안에서 실행
with app.app_context():
    # BookPoolCache 전역 객체 초기화
    book_pool_cache = BookPoolCache(db.session, Book)
    logger.info("[초기화] BookPoolCache 전역 객체 설정 완료")

    for message in consumer:
        try:
            raw_json = message.value

            if isinstance(raw_json, str):
                data = json.loads(raw_json)
            else:
                data = raw_json

            user_id = data.get('userId')
            read_books = data.get('readBooks', [])
            behavior = data.get('userBehaviors', [])

            logger.info(f"[Flask] Kafka 수신 메시지: {raw_json}")

            if not user_id:
                logger.error("Kafka 메시지에 userId 없음")
                continue

            if not isinstance(read_books, list) or not isinstance(behavior, list):
                logger.error(f"메시지 포맷 오류: readBooks 또는 behavior가 리스트가 아님")
                continue

            logger.info(f"Kafka 수신: userId={user_id}, 읽은 책 수={len(read_books)}, 행동 데이터 수={len(behavior)}")

            if not read_books:
                logger.warning(f"읽은 책 목록이 비어 있음: userId={user_id}")

            # 추천 도서 처리
            recommended_books = get_combined_recommendations(read_books, behavior, book_pool_cache)

            if recommended_books:
                logger.info(f"추천 완료: 추천 수={len(recommended_books)}")
                cache_recommendations(user_id, recommended_books)
                send_recommendations_to_kafka(user_id, recommended_books)
            else:
                logger.warning(f"추천 결과 없음: userId={user_id}")

        except Exception as e:
            logger.error(f"Kafka 메시지 처리 중 예외 발생: {e}", exc_info=True)
