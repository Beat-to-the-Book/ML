import json

def set_cache(redis_client, key, value, expiration):
    redis_client.set(key, json.dumps(value), ex=expiration)

def get_cache(redis_client, key):
    value = redis_client.get(key)
    return json.loads(value) if value else None
