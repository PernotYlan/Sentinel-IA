#!/usr/bin/env python3
"""
Script d'entrainement Autoencoder sur les evenements Zeek stockes dans PostgreSQL
Genere ae_model.keras et ae_scaler.pkl dans train/
A executer apres une semaine de collecte de donnees
"""

import json
import numpy as np
import pickle
import os
import sys
sys.path.insert(0, "/app")
import psycopg2
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers
from src.db import flush_events

load_dotenv(".env")

MODEL_OUT  = os.path.join(os.path.dirname(__file__), "ae_model.keras")
SCALER_OUT = os.path.join(os.path.dirname(__file__), "ae_scaler.pkl")
CLIENT_ID  = os.getenv("CLIENT_ID", "default")

FEATURES = ["orig_bytes", "resp_bytes", "duration", "orig_pkts", "resp_pkts",
            "src_port", "dst_port"]


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
        print("Aucun evenement trouve. Lancez Sentinel pendant une semaine d'abord.")
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


def build_autoencoder(input_dim: int) -> keras.Model:
    inputs  = keras.Input(shape=(input_dim,))
    encoded = layers.Dense(16, activation="relu")(inputs)
    encoded = layers.Dense(8, activation="relu")(encoded)
    latent  = layers.Dense(4, activation="relu")(encoded)
    decoded = layers.Dense(8, activation="relu")(latent)
    decoded = layers.Dense(16, activation="relu")(decoded)
    outputs = layers.Dense(input_dim, activation="linear")(decoded)
    return keras.Model(inputs, outputs)


def main():
    X = load_events()

    scaler   = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    model = build_autoencoder(X_scaled.shape[1])
    model.compile(optimizer="adam", loss="mse")

    print("\nEntrainement...")
    model.fit(X_scaled, X_scaled, epochs=50, batch_size=256, validation_split=0.1, verbose=1)

    reconstructed = model.predict(X_scaled)
    errors        = np.mean(np.square(X_scaled - reconstructed), axis=1)
    threshold     = float(np.mean(errors) + 2 * np.std(errors))
    print(f"\nSeuil d'anomalie: {threshold:.6f}")

    model.save(MODEL_OUT)
    with open(SCALER_OUT, "wb") as f:
        pickle.dump({"scaler": scaler, "threshold": threshold}, f)

    print(f"Modele sauvegarde: {MODEL_OUT}")
    print(f"Scaler sauvegarde: {SCALER_OUT}")

    flush_events()
    print("Table events videe pour le prochain cycle.")

if __name__ == "__main__":
    main()
