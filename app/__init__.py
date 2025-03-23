from flask import Flask, jsonify
from app.routes.recommend_routes import recommend_bp
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def root_health():
        return jsonify({"status": "OK"}), 200

    # 블루프린트 등록
    app.register_blueprint(recommend_bp, url_prefix="/recommend")

    return app
