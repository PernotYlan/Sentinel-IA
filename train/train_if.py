#!/usr/bin/env python3
"""
Script d'entrainement Isolation Forest sur les evenements Zeek stockes dans PostgreSQL
Genere if_model.pkl dans train/
Premier lancement: apres 30k evenements
Relance: toutes les 2 semaines via cron, flush de la table events apres
"""

import json
import numpy as np
import pickle
import os
import sys
sys.path.insert(0, "/app")
import psycopg2
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from src.db import flush_events

load_dotenv(".env")

MODEL_OUT  = os.path.join(os.path.dirname(__file__), "if_model.pkl")
CLIENT_ID  = os.getenv("CLIENT_ID", "default")


def load_events() -> np.ndarray:
    print(f"Chargement des evenements Zeek depuis PostgreSQL (schema: {CLIENT_ID})...")
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT", 5432)),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(f'SELECT raw FROM "{CLIENT_ID}".events WHERE source = %s', ('zeek',))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("Aucun evenement trouve.")
        exit(1)

    data = []
    for (raw,) in rows:
        e = raw if isinstance(raw, dict) else json.loads(raw)
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
    model = IsolationForest(contamination=float(os.getenv("IF_CONTAMINATION", "0.01")), random_state=42)
    model.fit(X)

    with open(MODEL_OUT, "wb") as f:
        pickle.dump(model, f)

    print(f"Modele sauvegarde: {MODEL_OUT}")

    flush_events()
    print("Table events videe pour le prochain cycle.")

if __name__ == "__main__":
    main()
