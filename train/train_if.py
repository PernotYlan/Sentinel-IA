#!/usr/bin/env python3
"""
Script d'entrainement Isolation Forest sur les evenements Zeek stockes dans buffer.db
Genere if_model.pkl dans train/
Premier lancement: apres 30k evenements
Relance: toutes les 2 semaines via cron, flush de la table events apres
"""

import sqlite3
import json
import numpy as np
import pickle
import os
import sys
sys.path.insert(0, "/app")
from sklearn.ensemble import IsolationForest

MODEL_OUT = os.path.join(os.path.dirname(__file__), "if_model.pkl")
DB_PATH   = "buffer.db"

def load_events() -> np.ndarray:
    """
    Charge tous les evenements Zeek depuis la table events de buffer.db
    Retourne un tableau numpy de shape (n_evenements, 7)
    """
    print("Chargement des evenements Zeek depuis buffer.db...")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT raw FROM events WHERE source = 'zeek'").fetchall()
    conn.close()

    if not rows:
        print("Aucun evenement trouve.")
        exit(1)

    data = []
    for (raw,) in rows:
        e = json.loads(raw)
        data.append([
            e.get("orig_bytes") or 0,
            e.get("resp_bytes") or 0,
            e.get("duration") or 0.0,
            e.get("orig_pkts") or 0,
            e.get("resp_pkts") or 0,
            e.get("src_port") or 0,
            e.get("dst_port") or 0,
        ])

    print(f"{len(data)} evenements charges.")
    return np.array(data, dtype=np.float32)

def main():
    X = load_events()

    print("\nEntrainement Isolation Forest...")
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    with open(MODEL_OUT, "wb") as f:
        pickle.dump(model, f)

    print(f"Modele sauvegarde: {MODEL_OUT}")

if __name__ == "__main__":
    main()
