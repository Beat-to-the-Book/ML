from flask import Flask, jsonify
from app.routes.hybrid_recommend_routes import recommend_bp
from app.routes.model_recommend_routes import model_recommend_bp
from app.core.config import Config
from app.core.logger import setup_logger
from app.core.extensions import db

logger = setup_logger()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # SQLAlchemy 초기화
    db.init_app(app)

    # Flask 기본 logger 수준 설정
    app.logger.setLevel(logger.level)

    @app.route("/")
    def root_health():
        return jsonify({"status": "OK"}), 200

    # 블루프린트 등록
    app.register_blueprint(recommend_bp, url_prefix="/recommend")
    app.register_blueprint(model_recommend_bp, url_prefix="/recommend")  # ← 이거 추가

    logger.info("Flask 앱 초기화 완료")

    return app
