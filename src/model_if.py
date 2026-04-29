import pickle
import os
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from src.features import extract_if
from src.logger import logger
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

load_dotenv(".env")

TRAIN_THRESHOLD = int(os.getenv("IF_TRAIN_THRESHOLD", "30000"))

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../train/if_model.pkl")

_contamination   = float(os.getenv("IF_CONTAMINATION", "0.01"))
model            = IsolationForest(contamination=_contamination, random_state=42)
trained          = False
loaded_from_disk = False

def _load_model():
    """
    Charge le modele IF depuis le disque si disponible
    """
    global model, trained, loaded_from_disk
    if not os.path.exists(MODEL_PATH):
        return
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        trained          = True
        loaded_from_disk = True
        logger.info("[IF] Modele charge depuis le disque")
    except Exception as e:
        logger.error(f"[IF] Erreur chargement modele: {e}")

class _ModelReloader(FileSystemEventHandler):
    """
    Recharge le modele IF automatiquement quand if_model.pkl est modifie
    """
    def on_modified(self, event):
        if event.src_path.endswith("if_model.pkl"):
            logger.info("[IF] Nouveau modele detecte, rechargement...")
            import time
            time.sleep(1)
            _load_model()

def init_if():
    """
    Charge le modele initial et demarre le watcher en arriere-plan
    """
    _load_model()
    observer = Observer()
    observer.schedule(_ModelReloader(), path=os.path.dirname(MODEL_PATH), recursive=False)
    observer.daemon = True
    observer.start()

def run_isolation_forest(window: deque):
    """
    Entraine et score la fenetre avec Isolation Forest
    -1 = anomalie, 1 = normal
    Attend TRAIN_THRESHOLD evenements avant d'entrainer le modele
    Si un modele existe sur disque, l'utilise directement sans attendre
    """
    global trained

    features = extract_if(window)

    if len(features) < 10:
        return None

    if not trained:
        if len(window) < TRAIN_THRESHOLD:
            logger.debug(f"[IF] Collecte de donnees... [{len(window)}/{TRAIN_THRESHOLD}]")
            return None
        model.fit(features)
        trained = True
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"[IF] Modele entraine et sauvegarde sur {TRAIN_THRESHOLD} evenements")
        return None

    scores = model.predict(features)
    anomaly_indices = [i for i, s in enumerate(scores) if s == -1]

    if anomaly_indices:
        logger.warning(f"[IF] {len(anomaly_indices)} anomalie(s) detectee(s) sur 10 evenements")
        return [list(window)[-10:][i] for i in anomaly_indices]
    else:
        logger.debug("[IF] Normal")
        return None
