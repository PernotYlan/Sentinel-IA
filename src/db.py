import sqlite3
import json

DB_PATH = "buffer.db"

def init_db():
    """
    Initialise la base de donnes SQLite et cree les tables si absentes
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unknown_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw       TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source    TEXT NOT NULL,
            raw       TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            src_ip    TEXT,
            model     TEXT NOT NULL,
            score     TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_event(source: str, data: dict):
    """
    Stocke un evenement parse dans la table events pour entrainement futur
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO events (source, raw) VALUES (?, ?)", (source, json.dumps(data)))
    conn.commit()
    conn.close()

def flush_events():
    """
    Vide la table events apres entrainement
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM events")
    conn.commit()
    conn.close()

def store_anomaly(src_ip: str, model: str, score: str):
    """
    Stocke une anomalie confirmee par IF+XGB ou IF+AE
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO anomalies (src_ip, model, score) VALUES (?, ?, ?)", (src_ip, model, score))
    conn.commit()
    conn.close()

def get_anomalies(limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, src_ip, model, score FROM anomalies ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def get_events(limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, source, timestamp, raw FROM events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def dump_sqlite(data: dict):
    """
    Insere un evenement non reconnu dans le buffer SQLite
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO unknown_events (raw) VALUES (?)", (json.dumps(data),))
    conn.commit()
    conn.close()
