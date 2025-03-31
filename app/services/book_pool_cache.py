from datetime import datetime, timedelta
from app.logger_config import setup_logger

logger = setup_logger()

class BookPoolCache:
    def __init__(self, db_session, book_model, expire_seconds=86400):
        self.db_session = db_session
        self.book_model = book_model
        self.expire_seconds = expire_seconds
        self.book_pool = []
        self.last_updated = datetime.min

    def get_book_pool(self):
        if datetime.now() - self.last_updated > timedelta(seconds=self.expire_seconds):
            logger.info("[BookPoolCache] 캐시 만료, DB에서 새로 조회 시작")

            try:
                books = self.db_session.query(self.book_model).all()
                self.book_pool = [book.to_dict() for book in books]
                self.last_updated = datetime.now()
                logger.info(f"[BookPoolCache] 조회된 책 수: {len(self.book_pool)}")
            except Exception as e:
                logger.error(f"[BookPoolCache] DB 조회 중 예외 발생: {e}", exc_info=True)

        return self.book_pool

# 전역 변수로 접근
book_pool_cache = None
