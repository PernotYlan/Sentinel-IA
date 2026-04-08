#!/usr/bin/env python3

from src.env import check_for_environment
from src.redis import connect_redis, receiver_redis
from src.db import init_db
from src.model_ae import init_ae

def main():
    """
    Execution de la boucle de logique principale
    """
    check_for_environment()
    ## TODO: add a return to check_for_environment() to handle in case of error
    init_db()
    init_ae()
    r = connect_redis()
    receiver_redis(r)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[91mArrêt du sentinel\033[00m")
