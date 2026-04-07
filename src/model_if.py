from sklearn.ensemble import IsolationForest
from src.features import extract_if
from collections import deque

TRAIN_THRESHOLD = 200
# //TODO: determine the TRAIN_THRESHHOLD -> maybe add to .env and param at start?

model = IsolationForest(contamination=0.05, random_state=42)
trained = False
# //TODO: determine the contamination lvl, this should be determined by SOC...

def run_isolation_forest(window: deque):
    """
    Entraine et score la fenetre avec Isolation Forest
    -1 = anomalie, 1 = normal
    Attend TRAIN_THRESHOLD evenements avant d'entrainer le modele
    """
    global trained
    features = extract_if(window)

    if len(features) < 10:
        return
    if not trained:
        if len(window) < TRAIN_THRESHOLD:
            print(f"\033[90m[IF] Collecte de donnees... [{len(window)}/{TRAIN_THRESHOLD}]\033[00m")
            return
        model.fit(features)
        trained = True
        print(f"\033[92m[IF] Modele entraine sur {TRAIN_THRESHOLD} evenements\033[00m")
    scores = model.predict(features)
    anomaly_indices = [i for i, s in enumerate(scores) if s == -1]
    if anomaly_indices:
        print(f"\033[91m[IF] {len(anomaly_indices)} anomalie(s) detectee(s) sur 10 evenements\033[00m")
        return [list(window)[-10:][i] for i in anomaly_indices]
    else:
        print(f"\033[92m[IF] Normal\033[00m")
        return None
