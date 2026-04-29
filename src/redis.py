import redis
import time
from dotenv import load_dotenv
from src.parser import parsing_service_selector
from src.logger import logger
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
            logger.info("Connexion Redis OK")
            return r
        except Exception as e:
            attempt += 1
            delay = min(RETRY_BASE ** attempt, RETRY_MAX)
            logger.warning(f"Erreur connexion Redis: {e} — nouvelle tentative dans {delay}s ({attempt}/{MAX_RETRIES})")
            if attempt >= MAX_RETRIES:
                logger.error("Nombre maximum de tentatives atteint, abandon.")
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
            result = r.blpop(os.getenv("REDIS_KEY"), timeout=5)
            if result is None:
                continue
            _, raw = result
            parsing_service_selector(raw)
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Connexion Redis perdue: {e} — reconnexion...")
            r = connect_redis()
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            time.sleep(2)
