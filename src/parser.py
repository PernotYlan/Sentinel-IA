import json
from collections import deque
from src.db import dump_sqlite, store_event, store_syslog
from src.logger import logger
from src.model_if import run_isolation_forest
import src.model_if as _model_if
from src.worker import submit_flagged

counters = {"zeek": 0, "syslog": 0, "db": 0}

zeek_window = deque(maxlen=30000)

def parse_zeek(data: dict) -> dict:
    """
    Extrait les champs pertinents d'un evenement Zeek brut vers un dictionnaire normalise
    """
    return {
        "src_ip": data.get("id.orig_h"),
        "dst_ip": data.get("id.resp_h"),
        "src_port": data.get("id.orig_p"),
        "dst_port": data.get("id.resp_p"),
        "proto": data.get("proto"),
        "service": data.get("service"),
        "duration": data.get("duration"),
        "orig_bytes": data.get("orig_bytes"),
        "resp_bytes": data.get("resp_bytes"),
        "conn_state": data.get("conn_state"),
        "orig_pkts": data.get("orig_pkts"),
        "resp_pkts": data.get("resp_pkts"),
        "timestamp": data.get("@timestamp")
    }

def parse_syslog(data: dict):
    hostname  = (data.get("host") or {}).get("name", "unknown")
    tenant_id = data.get("tenant_id")
    timestamp = data.get("@timestamp")

    inner = {}
    message = data.get("message", "")
    brace_idx = message.find("{")
    if brace_idx != -1:
        try:
            inner = json.loads(message[brace_idx:])
        except Exception:
            pass

    store_syslog(
        timestamp=timestamp,
        hostname=hostname,
        tenant_id=tenant_id,
        raw={"hostname": hostname, "tenant_id": tenant_id, "timestamp": timestamp, "metrics": inner},
    )

def parsing_service_selector(raw: str):
    """
    Route un evenement brut vers le bon parser selon les tags Filebeat/Zeek
    """
    data = json.loads(raw)
    tags = data.get("tags", [])

    if "zeek" in tags:
        parsed = parse_zeek(data)
        zeek_window.append(parsed)
        store_event("zeek", parsed)
        counters["zeek"] += 1
        logger.info(f"Zeek [{counters['zeek']}] - Window: [{len(zeek_window)}/30000]")
        if _model_if.loaded_from_disk or len(zeek_window) >= _model_if.TRAIN_THRESHOLD:
            flagged = run_isolation_forest(zeek_window)
            if flagged:
                submit_flagged(flagged)
    elif "beats_input_codec_plain_applied" in tags:
        parse_syslog(data)
        counters["syslog"] += 1
        logger.info(f"Syslog [{counters['syslog']}]")
    else:
        logger.debug(f"Tags inconnus: {tags}")
        dump_sqlite(data)
        counters["db"] += 1
        logger.info(f"DB [{counters['db']}]")
