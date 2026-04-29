import multiprocessing
from src.logger import logger

# // TODO: Container 1 = main process (Redis + zeek_window + IF), Container 2 = workers (XGB + AE)
# // TODO: passer N_WORKERS a 4 quand benchmark confirme le gain sur 2 coeurs

_pool = None
_worker_id = None
_id_counter = multiprocessing.Value('i', 0)


def _worker_init():
    import signal
    global _worker_id
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    with _id_counter.get_lock():
        _worker_id = _id_counter.value
        _id_counter.value += 1
    from src.db import init_db
    from src.model_ae import init_ae
    import src.model_xgb
    init_db()
    init_ae()


def _process_flagged(flagged: list):
    from src.model_xgb import run_xgb
    from src.model_ae import run_ae
    logger.info(f"[Worker-{_worker_id}] Traitement de {len(flagged)} evenement(s) suspects")
    run_xgb(flagged)
    run_ae(flagged)


def start_workers(n: int = 3):
    global _pool
    _pool = multiprocessing.Pool(processes=n, initializer=_worker_init)
    logger.info(f"[Workers] {n} worker(s) demarre(s)")


def submit_flagged(flagged: list):
    if _pool and flagged:
        _pool.apply_async(_process_flagged, args=(flagged,))


def stop_workers():
    if _pool:
        _pool.terminate()
        _pool.join()
