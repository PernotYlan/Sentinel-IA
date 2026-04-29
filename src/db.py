import json
import os
from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv(".env")

_CLIENT_ID = os.getenv("CLIENT_ID", "default")

_pg_pool: pool.ThreadedConnectionPool = None


def init_db():
    global _pg_pool
    _pg_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT", 5432)),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )
    _exec(f'CREATE SCHEMA IF NOT EXISTS "{_CLIENT_ID}"')
    _exec(f"""
        CREATE TABLE IF NOT EXISTS "{_CLIENT_ID}".events (
            id        SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            source    TEXT NOT NULL,
            raw       JSONB NOT NULL
        )
    """)
    _exec(f"""
        CREATE TABLE IF NOT EXISTS "{_CLIENT_ID}".anomalies (
            id        SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            src_ip    TEXT,
            model     TEXT NOT NULL,
            score     TEXT
        )
    """)
    _exec(f"""
        CREATE TABLE IF NOT EXISTS "{_CLIENT_ID}".unknown_events (
            id        SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            raw       JSONB NOT NULL
        )
    """)


def _exec(query: str, params=None):
    conn = _pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
    finally:
        _pg_pool.putconn(conn)


def store_event(source: str, data: dict):
    _exec(
        f'INSERT INTO "{_CLIENT_ID}".events (source, raw) VALUES (%s, %s)',
        (source, json.dumps(data))
    )


def flush_events():
    _exec(f'DELETE FROM "{_CLIENT_ID}".events')


def store_anomaly(src_ip: str, model: str, score: str):
    _exec(
        f'INSERT INTO "{_CLIENT_ID}".anomalies (src_ip, model, score) VALUES (%s, %s, %s)',
        (src_ip, model, score)
    )


def get_anomalies(limit: int = 50) -> list:
    conn = _pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT timestamp, src_ip, model, score FROM "{_CLIENT_ID}".anomalies ORDER BY id DESC LIMIT %s',
                (limit,)
            )
            return cur.fetchall()
    finally:
        _pg_pool.putconn(conn)


def get_events(limit: int = 50) -> list:
    conn = _pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id, source, timestamp, raw FROM "{_CLIENT_ID}".events ORDER BY id DESC LIMIT %s',
                (limit,)
            )
            return cur.fetchall()
    finally:
        _pg_pool.putconn(conn)


def dump_sqlite(data: dict):
    _exec(
        f'INSERT INTO "{_CLIENT_ID}".unknown_events (raw) VALUES (%s)',
        (json.dumps(data),)
    )
