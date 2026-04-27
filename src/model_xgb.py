from xgboost import XGBClassifier
from src.features import extract_xgb
from src.db import store_anomaly
from src.logger import logger
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../train/xgb_model.json")

model = XGBClassifier()
model.load_model(MODEL_PATH)

def run_xgb(flagged_events: list) -> int:
    """
    Score les evenements deja flagges par IF avec XGBoost pre-entraine
    0 = normal, 1 = attaque confirme
    """
    features = extract_xgb(flagged_events)
    X = np.array(features)
    scores = model.predict(X)
    confirmed = int(np.sum(scores))
    if confirmed > 0:
        logger.warning(f"[XGB] {confirmed} attaque(s) confirmee(s) sur {len(flagged_events)} evenements suspects")
        for i, s in enumerate(scores):
            if s == 1 and i < len(flagged_events):
                store_anomaly(flagged_events[i].get("src_ip", "-"), "XGB", "1")
    else:
        logger.info("[XGB] Faux positif IF - aucune attaque confirmee")
    return confirmed
