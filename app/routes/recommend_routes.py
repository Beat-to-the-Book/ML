from flask import Blueprint, jsonify, request
import requests
from app.services.recommend_cache_service import get_cached_recommendations, cache_recommendations
from app.config import Config

recommend_bp = Blueprint("recommend", __name__)

@recommend_bp.route("/<int:user_id>", methods=["GET"])
def get_recommendations(user_id):
    # Redis에서 추천 결과 확인
    recommendations = get_cached_recommendations(user_id)
    if recommendations:
        return jsonify(recommendations)

    # Spring Boot에 추천 요청 보내기
    try:
        response = requests.get(f"{Config.SPRING_BOOT_API}/recommend/{user_id}")
        response.raise_for_status()
        recommendations = response.json()

        # Redis에  결과 캐싱 (예: 10분)
        cache_recommendations(user_id, recommendations, expiration=600)

        return jsonify(recommendations)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
