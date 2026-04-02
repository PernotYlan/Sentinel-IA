import redis
from dotenv import load_dotenv
import os

def connect_redis():
    """
    Cree un HandShake entre Sentienl et Redis
    success: OK
    error: Erreur connexion Redis (int 1)
    """
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

def receiver_redis(r: redis.Redis):
    """
    Recoit raw data du stream Redis (Liste)
    """
    while 1:
        result = r.blpop(os.getenv("REDIS_KEY"), timeout=0)
        _, raw = result
        print(raw)