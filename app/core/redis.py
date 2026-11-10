import redis

from app.core.config import REDIS_URL


client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
