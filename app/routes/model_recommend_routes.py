from flask import Blueprint, jsonify, request
from app.infra.cache.redis_cache import set_cache
from app.models.book import Book
from app.repositories.book_repository import BookPoolRepository
from app.core.dependencies import db_session, redis_client
from app.services.model_based_recommender import ModelBasedRecommender
from app.utils.generate_training_dataset import append_training_row
import logging
from time import time

model_recommend_bp = Blueprint("model_recommend", __name__)
logger = logging.getLogger(__name__)

book_repository = BookPoolRepository(db_session=db_session, book_model=Book, redis_client=redis_client)
model_recommender = ModelBasedRecommender(book_repository=book_repository)

@model_recommend_bp.route("/", methods=["POST"])
def post_model_based_recommendations():
    data = request.get_json()
    user_id = data.get("userId")
    read_books = data.get("readBooks", [])
    user_behavior = data.get("userBehaviors", [])
    start_time = data.get("startTime")

    if not user_id or not read_books or not user_behavior:
        return jsonify({"error": "userId, readBooks, behavior 모두 필수입니다"}), 400

    recommendations = model_recommender.get_trained_recommendations(user_id, read_books, user_behavior)

    result = {
        "userId": user_id,
        "recommendedBooks": recommendations
    }

    # 사용자별 결과 캐싱
    set_cache(redis_client, f"recommend:trained:{user_id}", result)

    flask_end = time() * 1000
    if start_time:
        try:
            total_duration = round(flask_end - float(start_time))
            logger.info(f"[FLASK COMPLETE] userId={user_id}, 총 소요 시간={total_duration}ms (Spring→Flask→Kafka 전)")
        except Exception as e:
            logger.warning(f"[FLASK WARN] startTime 처리 중 오류: {e}")

    return jsonify(result)

@model_recommend_bp.route("/model/training-data", methods=["POST"])
def add_training_data():
    try:
        data = request.get_json()

        user_id = data.get("userId")
        behavior = data.get("behavior")
        read_books = data.get("readBooks")

        if not user_id or not behavior or not read_books:
            return jsonify({"error": "Missing fields"}), 400

        append_training_row(user_id, behavior, read_books)
        return jsonify({"message": "Row added to training_data.csv"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_recommend_bp.route("/model/train", methods=["POST"])
def train_model_api():
    try:
        from app.model.train_model import train_model_from_csv
        train_model_from_csv()
        return jsonify({"status": "success", "message": "모델 학습 완료"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})