import redis
import json
from app.config import Config

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

def get_user_actions(user_id):
    """사용자의 행동 데이터 가져오기"""
    key = f"user:{user_id}:actions"
    actions = redis_client.lrange(key, 0, -1)
    return [json.loads(action) for action in actions]

def store_user_action(user_id, action_data):
    """사용자 행동 데이터 저장"""
    key = f"user:{user_id}:actions"
    redis_client.rpush(key, json.dumps(action_data))
