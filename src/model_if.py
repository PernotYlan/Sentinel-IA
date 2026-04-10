import pickle
import os
from sklearn.ensemble import IsolationForest
from src.features import extract_if
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

TRAIN_THRESHOLD = 30000
# //TODO: determine the TRAIN_THRESHOLD -> maybe add to .env and param at start?

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../train/if_model.pkl")

model            = IsolationForest(contamination=0.05, random_state=42)
trained          = False
loaded_from_disk = False
# //TODO: determine the contamination lvl, this should be determined by SOC...

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
        print(f"\033[92m[IF] Modele charge depuis le disque\033[00m")
    except Exception as e:
        print(f"\033[91m[IF] Erreur chargement modele: {e}\033[00m")

class _ModelReloader(FileSystemEventHandler):
    """
    Recharge le modele IF automatiquement quand if_model.pkl est modifie
    """
    def on_modified(self, event):
        if event.src_path.endswith("if_model.pkl"):
            print(f"\033[94m[IF] Nouveau modele detecte, rechargement...\033[00m")
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
            print(f"\033[90m[IF] Collecte de donnees... [{len(window)}/{TRAIN_THRESHOLD}]\033[00m")
            return None
        model.fit(features)
        trained = True
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"\033[92m[IF] Modele entraine et sauvegarde sur {TRAIN_THRESHOLD} evenements\033[00m")
        return None

    scores = model.predict(features)
    anomaly_indices = [i for i, s in enumerate(scores) if s == -1]

    if anomaly_indices:
        print(f"\033[91m[IF] {len(anomaly_indices)} anomalie(s) detectee(s) sur 10 evenements\033[00m")
        return [list(window)[-10:][i] for i in anomaly_indices]
    else:
        print(f"\033[92m[IF] Normal\033[00m")
        return None
