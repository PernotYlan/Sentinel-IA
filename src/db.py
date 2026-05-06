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
            id          SERIAL PRIMARY KEY,
            timestamp   TIMESTAMPTZ DEFAULT NOW(),
            model       TEXT NOT NULL,
            attack_type TEXT,
            score       TEXT,
            src_ip      TEXT,
            dst_ip      TEXT,
            src_port    INT,
            dst_port    INT,
            proto       TEXT,
            service     TEXT,
            conn_state  TEXT,
            duration    FLOAT,
            orig_bytes  BIGINT,
            resp_bytes  BIGINT,
            raw         JSONB
        )
    """)
    _exec(f"""
        CREATE TABLE IF NOT EXISTS "{_CLIENT_ID}".unknown_events (
            id        SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            raw       JSONB NOT NULL
        )
    """)
    _exec(f"""
        CREATE TABLE IF NOT EXISTS "{_CLIENT_ID}".syslog (
            id         SERIAL PRIMARY KEY,
            timestamp  TIMESTAMPTZ NOT NULL,
            hostname   TEXT NOT NULL,
            tenant_id  TEXT,
            raw        JSONB NOT NULL
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


def store_anomalies_batch(rows: list):
    if not rows:
        return
    params = [
        (
            model, attack_type, score,
            event.get("src_ip"), event.get("dst_ip"),
            event.get("src_port"), event.get("dst_port"),
            event.get("proto"), event.get("service"), event.get("conn_state"),
            event.get("duration"), event.get("orig_bytes"), event.get("resp_bytes"),
            json.dumps(event),
        )
        for model, event, attack_type, score in rows
    ]
    conn = _pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                f"""INSERT INTO "{_CLIENT_ID}".anomalies
                    (model, attack_type, score, src_ip, dst_ip, src_port, dst_port,
                     proto, service, conn_state, duration, orig_bytes, resp_bytes, raw)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                params
            )
        conn.commit()
    finally:
        _pg_pool.putconn(conn)


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


def store_syslog(timestamp: str, hostname: str, tenant_id: str, raw: dict):
    _exec(
        f'INSERT INTO "{_CLIENT_ID}".syslog (timestamp, hostname, tenant_id, raw) VALUES (%s, %s, %s, %s)',
        (timestamp, hostname, tenant_id, json.dumps(raw))
    )


def flush_syslog_old(days: int = 30):
    _exec(f"DELETE FROM \"{_CLIENT_ID}\".syslog WHERE timestamp < NOW() - INTERVAL '{days} days'")


def dump_sqlite(data: dict):
    _exec(
        f'INSERT INTO "{_CLIENT_ID}".unknown_events (raw) VALUES (%s)',
        (json.dumps(data),)
    )
