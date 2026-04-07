#!/usr/bin/env python3
"""
Script d'entrainement XGBoost sur NSL-KDD + CICIDS2017
Genere un modele pre-entraine sauvegarde dans train/xgb_model.json
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import classification_report
import glob
import os

# Chemins des datasets
NSLKDD_TRAIN = os.path.expanduser("~/Documents/NSLKDD/KDDTrain+.txt")
NSLKDD_TEST  = os.path.expanduser("~/Documents/NSLKDD/KDDTest+.txt")
CICIDS_DIR   = os.path.expanduser("~/Documents/CICIDS2017/MachineLearningCVE/")
MODEL_OUT    = os.path.join(os.path.dirname(__file__), "xgb_model.json")

# Features cibles (memes que src/features.py extract_xgb)
FEATURES = ["orig_bytes", "resp_bytes", "duration", "orig_pkts", "resp_pkts",
            "src_port", "dst_port", "proto", "service", "conn_state"]

def encode(series: pd.Series) -> pd.Series:
    return series.astype(str).apply(lambda x: hash(x) % 1000)

# --- NSL-KDD ---
def load_nslkdd(path: str) -> pd.DataFrame:
    print(f"Chargement NSL-KDD: {path}")
    cols = ["duration", "proto", "service", "conn_state", "orig_bytes", "resp_bytes",
            "land", "wrong_fragment", "urgent", "hot",
            "num_failed_logins", "logged_in", "num_compromised", "root_shell",
            "su_attempted", "num_root", "num_file_creations", "num_shells",
            "num_access_files", "num_outbound_cmds", "is_host_login",
            "is_guest_login", "count", "srv_count", "serror_rate",
            "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
            "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
            "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
            "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
            "dst_host_serror_rate", "dst_host_srv_serror_rate",
            "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
            "label", "difficulty"]

    df = pd.read_csv(path, header=None, names=cols)
    df["label"]      = (df["label"] != "normal").astype(int)
    df["src_port"]   = 0
    df["dst_port"]   = 0
    df["orig_pkts"]  = 0
    df["resp_pkts"]  = 0
    df["proto"]      = encode(df["proto"])
    df["service"]    = encode(df["service"])
    df["conn_state"] = encode(df["conn_state"])
    return df[FEATURES + ["label"]]

# --- CICIDS2017 ---
def load_cicids(directory: str) -> pd.DataFrame:
    files = glob.glob(os.path.join(directory, "*.csv"))
    frames = []
    for f in files:
        print(f"Chargement CICIDS2017: {os.path.basename(f)}")
        df = pd.read_csv(f, low_memory=False)
        df.columns = df.columns.str.strip()
        out = pd.DataFrame()
        out["orig_bytes"]  = pd.to_numeric(df.get("Total Length of Fwd Packets", 0), errors="coerce").fillna(0)
        out["resp_bytes"]  = pd.to_numeric(df.get("Total Length of Bwd Packets", 0), errors="coerce").fillna(0)
        out["duration"]    = pd.to_numeric(df.get("Flow Duration", 0), errors="coerce").fillna(0)
        out["orig_pkts"]   = pd.to_numeric(df.get("Total Fwd Packets", 0), errors="coerce").fillna(0)
        out["resp_pkts"]   = pd.to_numeric(df.get("Total Backward Packets", 0), errors="coerce").fillna(0)
        out["src_port"]    = 0
        out["dst_port"]    = pd.to_numeric(df.get("Destination Port", 0), errors="coerce").fillna(0)
        out["proto"]       = 0
        out["service"]     = 0
        out["conn_state"]  = 0
        out["label"]       = (df["Label"].str.strip() != "BENIGN").astype(int)
        frames.append(out)
    return pd.concat(frames, ignore_index=True)

def main():
    # Charger et merger les deux datasets
    nsl_train = load_nslkdd(NSLKDD_TRAIN)
    nsl_test  = load_nslkdd(NSLKDD_TEST)
    cicids    = load_cicids(CICIDS_DIR)

    train = pd.concat([nsl_train, cicids], ignore_index=True)
    train = train.replace([np.inf, -np.inf], 0).fillna(0)
    nsl_test = nsl_test.replace([np.inf, -np.inf], 0).fillna(0)

    X_train = train[FEATURES].values
    y_train = train["label"].values
    X_test  = nsl_test[FEATURES].values
    y_test  = nsl_test["label"].values

    print(f"\nEntrainement sur {len(X_train)} exemples...")
    print(f"  Normal:  {int((y_train == 0).sum())}")
    print(f"  Attaque: {int((y_train == 1).sum())}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    print("\nEvaluation sur NSL-KDD test set:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Normal", "Attaque"]))

    model.save_model(MODEL_OUT)
    print(f"\nModele sauvegarde: {MODEL_OUT}")

if __name__ == "__main__":
    main()
