from app.core.logger import setup_logger
from app.infra.cache.redis_cache import get_cache, set_cache

logger = setup_logger()

class BookPoolRepository:
    def __init__(self, db_session, book_model, redis_client, expire_seconds=86400):
        self.db_session = db_session
        self.book_model = book_model
        self.redis_client = redis_client
        self.expire_seconds = expire_seconds
        self.cache_key = "book_pool_cache"

    def get_book_pool(self):
        # Redis에서 먼저 조회
        cached_data = get_cache(self.redis_client, self.cache_key)
        if cached_data:
            logger.info("[BookPoolRepository] Redis에서 책 목록 로드")
            return cached_data

        logger.info("[BookPoolRepository] Redis 캐시 없음 → DB 조회 시작")
        try:
            books = self.db_session.query(self.book_model).all()
            book_pool = [book.to_dict() for book in books]

            # Redis에 캐싱
            set_cache(self.redis_client, self.cache_key, book_pool, self.expire_seconds)
            logger.info(f"[BookPoolRepository] 조회된 책 수: {len(book_pool)}")
            return book_pool
        except Exception as e:
            logger.error(f"[BookPoolRepository] DB 조회 중 예외 발생: {e}", exc_info=True)
            return []
