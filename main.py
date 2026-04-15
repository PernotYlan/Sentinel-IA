#!/usr/bin/env python3

from src.env import check_for_environment
from src.redis import connect_redis, receiver_redis
from src.db import init_db
from src.worker import start_workers, stop_workers
from src.logger import logger
# from src.model_ae import init_ae
# from src.model_if import init_if

# // TODO: passer N_WORKERS a 4 quand le serveur avec 2 coeurs est disponible
# // TODO: migrer vers multiprocessing quand ML sera reactivee (IF zeek_window reste Container 1, XGB+AE dans Container 2)
N_WORKERS = 3

def main():
    """
    Execution de la boucle de logique principale
    """
    check_for_environment()
    ## TODO: add a return to check_for_environment() to handle in case of error
    init_db()
    # init_ae()
    # init_if()
    start_workers(N_WORKERS)
    r = connect_redis()
    receiver_redis(r)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Arrêt du sentinel")
        stop_workers(N_WORKERS)
