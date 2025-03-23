from redis import Redis
import json
from app.config import Config

redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

def get_cached_recommendations(user_id):
    """Redis에서 캐싱된 추천 데이터를 가져옴"""
    cached_data = redis_client.get(f"recommend:user:{user_id}")
    return json.loads(cached_data) if cached_data else None

def cache_recommendations(user_id, recommendations):
    """추천 데이터를 Redis에 캐싱"""
    redis_client.set(f"recommend:user:{user_id}", json.dumps(recommendations), ex=Config.CACHE_EXPIRE)
