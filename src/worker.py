import threading
import queue
from src.parser import parsing_service_selector
from src.logger import logger

# // TODO: Migrer vers multiprocessing.Queue quand le serveur sera disponible (2 coeurs)
# // TODO: Container 1 = consumer + zeek_window + IF, Container 2 = workers XGB + AE
# // TODO: N_WORKERS cible = 4 workers sur 2 coeurs (2 workers/coeur)
_event_queue: queue.Queue = queue.Queue()

def get_queue() -> queue.Queue:
    """
    Retourne la queue partagee entre le producteur et les workers
    """
    return _event_queue

def _worker_loop(worker_id: int):
    """
    Boucle d'un worker: consomme les evenements de la queue et les traite
    """
    # // TODO: remplacer threading par multiprocessing.Process ici pour vrai parallelisme ML
    logger.info(f"[Worker-{worker_id}] Demarrage")
    while True:
        try:
            raw = _event_queue.get(timeout=1)
            if raw is None:
                logger.info(f"[Worker-{worker_id}] Signal d'arret recu")
                break
            logger.info(f"[Worker-{worker_id}] Traitement evenement (queue: {_event_queue.qsize()})")
            parsing_service_selector(raw)
            _event_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"[Worker-{worker_id}] Erreur traitement evenement: {e}")
            _event_queue.task_done()

def start_workers(n: int = 3) -> list[threading.Thread]:
    """
    Demarre n threads workers et retourne la liste des threads
    """
    # // TODO: passer a 4 workers quand 2 coeurs disponibles sur le serveur
    threads = []
    for i in range(n):
        t = threading.Thread(target=_worker_loop, args=(i,), daemon=True, name=f"Worker-{i}")
        t.start()
        threads.append(t)
    logger.info(f"[Workers] {n} worker(s) demarre(s)")
    return threads

def stop_workers(n: int):
    """
    Envoie n signaux d'arret dans la queue pour stopper les workers proprement
    """
    for _ in range(n):
        _event_queue.put(None)
