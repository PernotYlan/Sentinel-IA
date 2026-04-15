import redis
import time
from dotenv import load_dotenv
from src.worker import get_queue
import os

MAX_RETRIES = 10
RETRY_BASE  = 2  # secondes, exponentiel: 2, 4, 8, 16...
RETRY_MAX   = 60 # plafond en secondes

# // TODO: Oublie pas de tester la logique de reconnection pas eut la possibilite avec le test 2 sem...
def connect_redis() -> redis.Redis:
    """
    Cree un HandShake entre Sentinel et Redis
    Retente automatiquement avec backoff exponentiel si Redis est indisponible
    """
    load_dotenv(".env")
    attempt = 0
    while True:
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
            attempt += 1
            delay = min(RETRY_BASE ** attempt, RETRY_MAX)
            print(f"\033[91mErreur connexion Redis: {e} — nouvelle tentative dans {delay}s ({attempt}/{MAX_RETRIES})\033[00m")
            if attempt >= MAX_RETRIES:
                print("\033[91mNombre maximum de tentatives atteint, abandon.\033[00m")
                exit(1)
            time.sleep(delay)


def receiver_redis(r: redis.Redis):
    """
    Recoit raw data du stream Redis (Liste)
    Reconnecte automatiquement si la connexion est perdue
    """
    load_dotenv(".env")
    while True:
        try:
            result = r.blpop(os.getenv("REDIS_KEY"), timeout=0)
            _, raw = result
            get_queue().put(raw)
        except redis.exceptions.ConnectionError as e:
            print(f"\033[91mConnexion Redis perdue: {e} — reconnexion...\033[00m")
            r = connect_redis()
        except Exception as e:
            print(f"\033[91mErreur inattendue: {e}\033[00m")
            time.sleep(2)
