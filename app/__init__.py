from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.routes.recommend_routes import recommend_bp
from app.config import Config
import logging
from app.logger_config import setup_logger

db = SQLAlchemy()
logger = setup_logger()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # SQLAlchemy 초기화
    db.init_app(app)

    # Flask 기본 logger 수준 설정
    app.logger.setLevel(logger.level)

    # 순환 참조 방지 import
    from app.models.book import Book
    from app.services.book_pool_cache import BookPoolCache, book_pool_cache

    # BookPoolCache 전역 객체 초기화
    with app.app_context():
        book_pool_cache = BookPoolCache(db.session, Book)
        logger.info("BookPoolCache 초기화 완료")

    # 상태 확인용 엔드포인트
    @app.route("/")
    def root_health():
        return jsonify({"status": "OK"}), 200

    # 블루프린트 등록
    app.register_blueprint(recommend_bp, url_prefix="/recommend")

    logger.info("Flask 앱 초기화 완료")

    return app
