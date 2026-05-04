import json
import os
import redis as _redis
from dotenv import load_dotenv
from src.logger import logger

load_dotenv(".env")

_r = None


def _get_redis():
    global _r
    if _r is None:
        _r = _redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
    return _r


def flagged_key() -> str:
    return f"sentinel:flagged:{os.getenv('CLIENT_ID', 'default')}"


def submit_flagged(flagged: list):
    try:
        _get_redis().rpush(flagged_key(), json.dumps(flagged))
    except Exception as e:
        logger.error(f"[Core] Erreur envoi events flagges vers workers: {e}")
