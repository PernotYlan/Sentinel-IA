import redis
from dotenv import load_dotenv
import os

def connect_redis():
    load_dotenv(".env")
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        r.ping()
        print("\033[92mConnexion Redis OK\033[00m")
        return r
    except Exception as e:
        print(f"\033[91mErreur connexion Redis: {e}\033[00m")
        exit(1)
