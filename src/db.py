import sqlite3
import json

DB_PATH = "buffer.db"

def init_db():
    """
    Initialise la base de donnes SQLite et cree la table si absente
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unknown_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw       TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def dump_sqlite(data: dict):
    """
    Insere un evenement non reconnu dans le buffer SQLite
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO unknown_events (raw) VALUES (?)", (json.dumps(data),))
    conn.commit()
    conn.close()
