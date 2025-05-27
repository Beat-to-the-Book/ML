from flask import Blueprint, jsonify, request
from app.services.recommend_cache import get_cached_recommendations, cache_recommendations
from app.services.recommend_service import get_combined_recommendations
from app.services.book_pool_cache import book_pool_cache
from time import time

recommend_bp = Blueprint("recommend", __name__)

@recommend_bp.route("/", methods=["POST"])
def post_recommendations():
    data = request.get_json()
    user_id = data.get("userId")
    read_books = data.get("readBooks", [])
    user_behavior = data.get("userBehaviors", [])

    if not user_id or not read_books or not user_behavior:
        return jsonify({"error": "userId, readBooks, behavior 모두 필수입니다"}), 400

    recommendations = get_combined_recommendations(
        read_books,
        user_behavior,
        book_pool_cache,
        alpha=0.5
    )

    result = {
        "userId": user_id,
        "recommendedBooks": recommendations
    }

    cache_recommendations(user_id, result)
    return jsonify(result)
