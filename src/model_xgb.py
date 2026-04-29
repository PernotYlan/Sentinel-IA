from xgboost import XGBClassifier
from src.features import extract_xgb
from src.db import store_anomaly
from src.logger import logger
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../train/xgb_model.json")

_model = None


def _load_model():
    global _model
    if not os.path.exists(MODEL_PATH):
        return
    try:
        m = XGBClassifier()
        m.load_model(MODEL_PATH)
        _model = m
        logger.info("[XGB] Modele charge")
    except Exception as e:
        logger.error(f"[XGB] Erreur chargement modele: {e}")

_load_model()


def run_xgb(flagged_events: list) -> int:
    if _model is None:
        return 0
    features = extract_xgb(flagged_events)
    X = np.array(features)
    scores = _model.predict(X)
    confirmed = int(np.sum(scores))
    if confirmed > 0:
        logger.warning(f"[XGB] {confirmed} attaque(s) confirmee(s) sur {len(flagged_events)} evenements suspects")
        for i, s in enumerate(scores):
            if s == 1 and i < len(flagged_events):
                store_anomaly(flagged_events[i].get("src_ip", "-"), "XGB", "1")
    else:
        logger.info("[XGB] Faux positif IF - aucune attaque confirmee")
    return confirmed
