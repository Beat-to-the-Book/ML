from kafka import KafkaConsumer
import json
from app import create_app, db
from app.models.book import Book
from app.services.book_pool_cache import BookPoolCache, book_pool_cache as global_cache
from app.services.recommend_service import get_similar_books_from_multiple
from app.services.recommend_cache import cache_recommendations
from app.services.kafka_producer import send_recommendations_to_kafka
from app.config import Config
from app.logger_config import setup_logger

logger = setup_logger()
app = create_app()

# Kafka Consumer: Spring에서 도서 리스트를 받음
consumer = KafkaConsumer(
    'recommendation_topic',
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
            data = message.value
            logger.info(f"[RAW] Kafka 수신 메시지: {data}")

            user_id = data.get('userId')
            books = data.get('books', [])
            logger.info(f"파싱된 userId={user_id}, books 수={len(books)}")

            if not user_id:
                logger.error("Kafka 메시지에 userId 없음")
                continue

            if not isinstance(books, list):
                logger.error(f"books 형식 오류: type={type(books)}, 값={books}")
                continue

            logger.info(f"Kafka 수신: userId={user_id}, 받은 도서 수={len(books)}")

            if not books:
                logger.warning(f"books 비어 있음: userId={user_id}")
                continue

            # 추천 도서 처리
            recommended_books = get_similar_books_from_multiple(books, global_cache)
            cache_recommendations(user_id, recommended_books)

            logger.info(f"유사 도서 계산 완료: userId={user_id}, 추천 수={len(recommended_books)}")

            if recommended_books:
                send_recommendations_to_kafka(user_id, recommended_books)
            else:
                logger.warning(f"추천 도서 없음: userId={user_id}")

        except Exception as e:
            logger.error(f"Kafka 메시지 처리 중 예외 발생: {e}", exc_info=True)
