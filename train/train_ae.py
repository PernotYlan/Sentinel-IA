#!/usr/bin/env python3
"""
Script d'entrainement Autoencoder sur les evenements Zeek stockes dans buffer.db
Genere ae_model.keras et ae_scaler.pkl dans train/
A executer apres une semaine de collecte de donnees
"""

import sqlite3
import json
import numpy as np
import pickle
import os
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers

DB_PATH    = "buffer.db"
MODEL_OUT  = os.path.join(os.path.dirname(__file__), "ae_model.keras")
SCALER_OUT = os.path.join(os.path.dirname(__file__), "ae_scaler.pkl")

# Les features numeriques extraites de chaque evenement Zeek
FEATURES = ["orig_bytes", "resp_bytes", "duration", "orig_pkts", "resp_pkts",
            "src_port", "dst_port"]

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
        print("Aucun evenement trouve. Lancez Sentinel pendant une semaine d'abord.")
        exit(1)

    data = []
    for (raw,) in rows:
        # Chaque ligne est un JSON stringify, on le parse en dict
        e = json.loads(raw)
        # On extrait les 7 valeurs numeriques, 0 si absentes
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
    # Conversion en tableau numpy float32 pour tensorflow
    return np.array(data, dtype=np.float32)

def build_autoencoder(input_dim: int) -> keras.Model:
    """
    Construit l'architecture de l'autoencoder:
    - Encodeur: compresse les donnees de input_dim -> 16 -> 8 -> 4 (espace latent)
    - Decodeur: reconstruit les donnees de 4 -> 8 -> 16 -> input_dim
    Le modele apprend a reconstruire du trafic normal
    Un trafic anormal sera mal reconstruit -> erreur elevee -> anomalie
    """
    inputs = keras.Input(shape=(input_dim,))

    # Encodeur: compression progressive
    encoded = layers.Dense(16, activation="relu")(inputs)
    encoded = layers.Dense(8, activation="relu")(encoded)
    latent  = layers.Dense(4, activation="relu")(encoded) # espace latent (representation compressée)

    # Decodeur: reconstruction progressive
    decoded = layers.Dense(8, activation="relu")(latent)
    decoded = layers.Dense(16, activation="relu")(decoded)
    outputs = layers.Dense(input_dim, activation="linear")(decoded) # sortie = meme taille que l'entree

    return keras.Model(inputs, outputs)

def main():
    # Chargement des donnees brutes
    X = load_events()

    # Normalisation: ramene toutes les valeurs entre 0 et 1
    # Le scaler "apprend" les min/max de chaque feature sur les donnees d'entrainement
    # Il faut sauvegarder ce scaler pour appliquer la meme normalisation a runtime
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Construction et compilation du modele
    # loss="mse" = mean squared error: mesure l'ecart entre entree et reconstruction
    model = build_autoencoder(X_scaled.shape[1])
    model.compile(optimizer="adam", loss="mse")
    model.summary()

    # Entrainement: le modele apprend a reconstruire X a partir de X
    # validation_split=0.1 = 10% des donnees reservees pour valider sans entrainer
    print("\nEntrainement...")
    model.fit(X_scaled, X_scaled, epochs=50, batch_size=256, validation_split=0.1, verbose=1)

    # Calcul du seuil d'anomalie sur les donnees d'entrainement
    # Pour chaque evenement: erreur = moyenne des carres des differences (entree vs reconstruction)
    # Seuil = mean + 2*std: tout ce qui depasse ce seuil a runtime sera considere anomalie
    reconstructed = model.predict(X_scaled)
    errors = np.mean(np.square(X_scaled - reconstructed), axis=1)
    threshold = float(np.mean(errors) + 2 * np.std(errors))
    print(f"\nSeuil d'anomalie: {threshold:.6f}")

    # Sauvegarde du modele et du scaler+seuil dans un seul fichier pkl
    model.save(MODEL_OUT)
    with open(SCALER_OUT, "wb") as f:
        pickle.dump({"scaler": scaler, "threshold": threshold}, f)

    print(f"Modele sauvegarde: {MODEL_OUT}")
    print(f"Scaler sauvegarde: {SCALER_OUT}")

if __name__ == "__main__":
    main()
