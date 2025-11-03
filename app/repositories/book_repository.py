from app.core.logger import setup_logger
from app.infra.cache.redis_cache import get_cache, set_cache

logger = setup_logger()

class BookPoolRepository:
    def __init__(self, db_session, book_model, redis_client, expire_seconds=86400, cache_key="book_pool_cache"):
        self.db_session = db_session
        self.book_model = book_model
        self.redis_client = redis_client
        self.expire_seconds = expire_seconds
        self.cache_key = cache_key

    def get_book_pool(self):
        # Redis에 book_pool만 캐싱한다.
        cached = get_cache(self.redis_client, self.cache_key)
        if cached:
            logger.info("[BookPoolRepository] Redis에서 book_pool 로드")
            return cached

        logger.info("[BookPoolRepository] Redis 캐시 미스 → DB 조회 시작")
        try:
            books = self.db_session.query(self.book_model).all()
            book_pool = [book.to_dict() for book in books]

            # Redis에 캐싱
            set_cache(self.redis_client, self.cache_key, book_pool, self.expire_seconds)
            logger.info(f"[BookPoolRepository] DB 조회 후 캐시 적재 완료 (count={len(book_pool)})")
            return book_pool
        except Exception as e:
            logger.error(f"[BookPoolRepository] DB 조회 예외: {e}", exc_info=True)
            return []
