from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.routes.recommend_routes import recommend_bp
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.route("/")
    def root_health():
        return jsonify({"status": "OK"}), 200

    # 블루프린트 등록
    app.register_blueprint(recommend_bp, url_prefix="/recommend")

    return app
