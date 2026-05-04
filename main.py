#!/usr/bin/env python3
import os
import signal
import threading
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

RED   = "\033[91m"
CYAN  = "\033[96m"
RESET = "\033[0m"

_start_time = None


def _test_training():
    for i in range(10):
        print(f"{RED}[TEST] Pre-entrainement IF — message {i+1}/10{RESET}", flush=True)
    import train.train_ae as _train_ae
    _train_ae.main()
    for i in range(10):
        print(f"{CYAN}[TEST] Post-entrainement IF — message {i+1}/10{RESET}", flush=True)


def main():
    global _start_time
    _start_time = time.time()
    check_for_environment()
    init_db()
    init_if()
    if os.getenv("TEST_TRAINING") == "1":
        threading.Timer(10.0, _test_training).start()
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
