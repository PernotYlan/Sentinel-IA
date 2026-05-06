#!/usr/bin/env python3
"""
Script d'entrainement XGBoost multiclasse sur UNSW-NB15
Genere xgb_model.json et xgb_labels.json dans train/

Fichiers attendus dans train/data/:
  UNSW_NB15_training-set.csv (telecharge depuis Hugging Face Mouwiya/UNSW-NB15)
"""

import json
import numpy as np
import pandas as pd
import os
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from src.features import encode

load_dotenv(".env")

MODEL_OUT  = os.path.join(os.path.dirname(__file__), "xgb_model.json")
LABELS_OUT = os.path.join(os.path.dirname(__file__), "xgb_labels.json")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")


def load_dataset() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv")
    if not os.path.exists(path):
        print(f"Fichier introuvable: {path}")
        exit(1)
    print(f"Chargement {os.path.basename(path)}...")
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip().str.lstrip("﻿")
    print(f"{len(df)} lignes chargees.")
    return df


def build_features(df: pd.DataFrame) -> np.ndarray:
    # sport/dsport absent de ce CSV — mis a 0, le modele ignorera ces features
    return np.column_stack([
        pd.to_numeric(df["sbytes"],  errors="coerce").fillna(0).values,
        pd.to_numeric(df["dbytes"],  errors="coerce").fillna(0).values,
        pd.to_numeric(df["dur"],     errors="coerce").fillna(0).values,
        pd.to_numeric(df["spkts"],   errors="coerce").fillna(0).values,
        pd.to_numeric(df["dpkts"],   errors="coerce").fillna(0).values,
        np.zeros(len(df)),  # src_port
        np.zeros(len(df)),  # dst_port
        df["proto"].map(encode).values,
        df["service"].map(encode).values,
        df["state"].map(encode).values,
    ]).astype(np.float32)


def main():
    df = load_dataset()

    df["attack_cat"] = df["attack_cat"].fillna("Normal").astype(str).str.strip()

    # Normal = 0, attacks sorted alphabetically after
    attack_types  = sorted([c for c in df["attack_cat"].unique() if c != "Normal"])
    categories    = ["Normal"] + attack_types
    label_map     = {cat: i for i, cat in enumerate(categories)}
    label_map_inv = {i: cat for i, cat in enumerate(categories)}
    print(f"\nCategories ({len(categories)}): {categories}")

    y = df["attack_cat"].map(label_map).values.astype(int)

    print("\nExtraction des features...")
    X = build_features(df)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nEntrainement XGBoost ({len(categories)} classes, {len(X_train)} exemples)...")
    model = XGBClassifier(
        objective="multi:softmax",
        num_class=len(categories),
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        n_jobs=-1,
        random_state=42,
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=10)

    y_pred = model.predict(X_test)
    print("\nRapport de classification:")
    print(classification_report(y_test, y_pred, target_names=categories))

    model.save_model(MODEL_OUT)
    with open(LABELS_OUT, "w") as f:
        json.dump(label_map_inv, f, indent=2)

    print(f"\nModele sauvegarde: {MODEL_OUT}")
    print(f"Labels sauvegardes: {LABELS_OUT}")


if __name__ == "__main__":
    main()
