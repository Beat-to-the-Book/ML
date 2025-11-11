# 사용 X
# Kafka Consumer에서 메시지를 수신하면, 추천 로직 실행
from flask import Blueprint, jsonify, request
from app.infra.cache.redis_cache import set_cache
from app.models.book import Book
from app.repositories.book_repository import BookPoolRepository
from app.core.dependencies import db_session, redis_client
from app.services.model_based_recommender import ModelBasedRecommender
from app.utils.generate_training_dataset import append_training_row
from app.utils.train_model import train_model_from_csv
from app.utils.generate_reason import generate_reason
import logging
from time import time
import json

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

    recommendations = model_recommender.get_model_based_recommendations(read_books, user_behavior)

    # 추천 결과 캐시
    result = {
        "userId": user_id,
        "recommendedBooks": recommendations
    }
    set_cache(redis_client, f"recommend:trained:{user_id}", result)

    # 사용자 데이터 캐시
    context_data = {
        "readBooks": read_books,
        "userBehaviors": user_behavior
    }
    set_cache(redis_client, f"user_context:{user_id}", context_data)

    flask_end = time() * 1000
    if start_time:
        try:
            total_duration = round(flask_end - float(start_time))
            logger.info(f"[FLASK COMPLETE] userId={user_id}, 총 소요 시간={total_duration}ms (Spring→Flask→Kafka 전)")
        except Exception as e:
            logger.warning(f"[FLASK WARN] startTime 처리 중 오류: {e}")

    return jsonify(result)

@model_recommend_bp.route("/reason", methods=["POST"])
def post_recommendation_reason():
    data = request.get_json()
    logger.info("[FLASK] /recommend/reason 요청 수신: %s", data)

    user_id = data.get("userId")
    recommended_books = data.get("recommendedBooks", [])

    if not user_id or not recommended_books:
        return jsonify({"error": "userId, recommendedBooks 필수"}), 400

    # Redis에 저장된 사용자 행동 로그 및 읽은 책 정보 조회
    user_context = redis_client.get(f"user_context:{user_id}")
    if user_context is None:
        logger.info("[FLASK] Redis에서 불러온 user_context: %s", user_context)
        return jsonify({"error": "사용자 행동 정보가 없습니다"}), 404

    try:
        context = json.loads(user_context)
    except Exception as e:
        logger.error("[FLASK] user_context JSON 파싱 에러: %s", str(e))
        return jsonify({"error": "Redis 데이터 파싱 실패"}), 500

    read_books = context.get("readBooks", [])
    behaviors = context.get("userBehaviors", [])

    logger.info("[FLASK] 읽은 책 개수: %d", len(read_books))
    logger.info("[FLASK] 사용자 행동 로그 개수: %d", len(behaviors))

    result = []
    for book in recommended_books:
        reason = generate_reason(read_books, behaviors, book.get("title"), book.get("score"))
        result.append({
            "bookId": book.get("bookId"),
            "title": book.get("title"),
            "author": book.get("author"),
            "coverImageUrl": book.get("coverImageUrl"),
            "reason": reason
        })

    return jsonify({"booksWithReason": result})

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
        train_model_from_csv()
        return jsonify({"status": "success", "message": "모델 학습 완료"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})