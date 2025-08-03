from flask import Blueprint, jsonify, request
from app.infra.cache.redis_cache import set_cache
from app.services.semantic_hybrid_recommender import SemanticHybridRecommender
from app.repositories.book_repository import BookPoolRepository
from app.core.dependencies import db_session, redis_client
from app.models.book import Book
import logging
from time import time

recommend_bp = Blueprint("recommend", __name__)
logger = logging.getLogger(__name__)

# --- 전역 객체 초기화 ---
book_repository = BookPoolRepository(db_session=db_session, book_model=Book, redis_client=redis_client)
recommender = SemanticHybridRecommender(book_repository=book_repository)

@recommend_bp.route("/", methods=["POST"])
def post_recommendations():
    data = request.get_json()
    user_id = data.get("userId")
    read_books = data.get("readBooks", [])
    user_behavior = data.get("userBehaviors", [])
    start_time = data.get("startTime")

    if not user_id or not read_books or not user_behavior:
        return jsonify({"error": "userId, readBooks, behavior 모두 필수입니다"}), 400

    recommendations = recommender.get_semantic_hybrid_recommendations(read_books, user_behavior)

    result = {
        "userId": user_id,
        "recommendedBooks": recommendations
    }

    set_cache(redis_client, f"recommend:user:{user_id}", result)

    flask_end = time() * 1000
    if start_time:
        try:
            total_duration = round(flask_end - float(start_time))
            logger.info(f"[FLASK COMPLETE] userId={user_id}, 총 소요 시간={total_duration}ms (Spring→Flask→Kafka 전)")
        except Exception as e:
            logger.warning(f"[FLASK WARN] startTime 처리 중 오류: {e}")

    return jsonify(result)
