#!/usr/bin/env python3
import json
import multiprocessing
import os
import signal
import time

def _handle_sigterm(sig, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, _handle_sigterm)

import redis
from dotenv import load_dotenv

from src.logger import logger

load_dotenv(".env")

N_WORKERS = int(os.getenv("N_WORKERS", 3))


def _flagged_key() -> str:
    return f"sentinel:flagged:{os.getenv('CLIENT_ID', 'default')}"


def _worker_loop(worker_id: int):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    from src.db import init_db
    from src.model_ae import init_ae
    import src.model_xgb
    from src.model_xgb import run_xgb
    from src.model_ae import run_ae

    init_db()
    init_ae()

    r = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )

    key = _flagged_key()
    logger.info(f"[Worker-{worker_id}] Pret, en attente sur {key}")

    while True:
        try:
            result = r.blpop(key, timeout=5)
            if result is None:
                continue
            _, raw = result
            flagged = json.loads(raw)
            logger.info(f"[Worker-{worker_id}] Traitement de {len(flagged)} evenement(s) suspects")
            run_xgb(flagged)
            run_ae(flagged)
        except redis.exceptions.ConnectionError as e:
            logger.error(f"[Worker-{worker_id}] Redis perdu: {e} — reconnexion dans 2s...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"[Worker-{worker_id}] Erreur: {e}")


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    processes = []

    for i in range(N_WORKERS):
        p = multiprocessing.Process(target=_worker_loop, args=(i,), name=f"Worker-{i}")
        p.start()
        processes.append(p)
        logger.info(f"[Workers] Worker-{i} demarre (PID {p.pid})")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        elapsed_msg = ""
        logger.info(f"Arret des workers")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
