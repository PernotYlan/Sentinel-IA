import numpy as np
import pickle
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../train/ae_model.keras")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "../train/ae_scaler.pkl")

model = None
scaler = None
threshold = None

def _load_model():
    """
    Charge ou recharge le modele AE et le scaler depuis le disque
    """
    global model, scaler, threshold
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return
    try:
        from tensorflow import keras
        model = keras.models.load_model(MODEL_PATH)
        with open(SCALER_PATH, "rb") as f:
            data = pickle.load(f)
            scaler = data["scaler"]
            threshold = data["threshold"]
        print(f"\033[92m[AE] Modele charge (seuil: {threshold:.6f})\033[00m")
    except Exception as e:
        print(f"\033[91m[AE] Erreur chargement modele: {e}\033[00m")

class _ModelReloader(FileSystemEventHandler):
    """
    Recharge le modele AE automatiquement quand ae_model.keras est modifie
    """
    def on_modified(self, event):
        if event.src_path.endswith("ae_model.keras"):
            print(f"\033[94m[AE] Nouveau modele detecte, rechargement...\033[00m")
            _load_model()

def init_ae():
    """
    Charge le modele initial et demarre le watcher en arriere-plan
    """
    _load_model()
    observer = Observer()
    observer.schedule(_ModelReloader(), path=os.path.dirname(MODEL_PATH), recursive=False)
    observer.daemon = True
    observer.start()

def run_ae(flagged_events: list):
    """
    Score les evenements deja flagges par IF avec l'autoencoder
    Anomalie = erreur de reconstruction > seuil
    """
    if model is None or scaler is None:
        return

    features = np.array([
        [
            e.get("orig_bytes") or 0,
            e.get("resp_bytes") or 0,
            e.get("duration") or 0.0,
            e.get("orig_pkts") or 0,
            e.get("resp_pkts") or 0,
            e.get("src_port") or 0,
            e.get("dst_port") or 0,
        ]
        for e in flagged_events
    ], dtype=np.float32)

    X = scaler.transform(features)
    reconstructed = model.predict(X, verbose=0)
    errors = np.mean(np.square(X - reconstructed), axis=1)
    anomalies = int(np.sum(errors > threshold))

    if anomalies > 0:
        print(f"\033[91m[AE] {anomalies} anomalie(s) confirmee(s) sur {len(flagged_events)} evenements suspects\033[00m")
    else:
        print(f"\033[93m[AE] Faux positif IF - aucune anomalie confirmee\033[00m")
