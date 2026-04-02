#!/usr/bin/env python3

from src.env import check_for_environment
from src.redis import connect_redis

def main():
    """
    Execution de la boucle de logique principale
    """
    check_for_environment()
    ## TODO: add a return to check_for_environment() to handle in case of error
    r = connect_redis()

if __name__ == "__main__":
    main()
