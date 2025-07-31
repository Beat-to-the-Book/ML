from redis import Redis
import json
from app.core.config import Config

redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

# 추천 데이터를 Redis에 캐싱
def cache_recommendations(user_id, recommendations, expiration=600):
    redis_client.set(
        f"recommend:user:{user_id}",
        json.dumps(recommendations),
        ex=expiration
    )
