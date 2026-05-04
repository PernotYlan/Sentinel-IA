#!/usr/bin/env python3
import os
import signal
import time

def _handle_sigterm(sig, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, _handle_sigterm)

from src.env import check_for_environment
from src.redis import connect_redis, receiver_redis
from src.db import init_db
from src.logger import logger
from src.model_if import init_if
import src.parser as _parser

_start_time = None


def main():
    global _start_time
    _start_time = time.time()
    check_for_environment()
    init_db()
    init_if()
    r = connect_redis()
    receiver_redis(r)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        elapsed = (time.time() - (_start_time or time.time())) / 60
        zeek = _parser.counters["zeek"]
        rate = zeek / elapsed if elapsed > 0 else 0
        logger.info(f"Arret — {zeek} events Zeek | {elapsed:.1f} min | {rate:.0f} events/min")
