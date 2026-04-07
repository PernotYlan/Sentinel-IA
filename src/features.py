from collections import deque

def encode(value) -> int:
    if value is None:
        return 0
    return hash(str(value)) % 1000

def extract_xgb(events: list) -> list:
    """
    Extraction des features pour XGBoost
    Numeriques + categoriques encodes, liste d'evenements flagges par IF
    """
    return [
        [
            e.get("orig_bytes") or 0,
            e.get("resp_bytes") or 0,
            e.get("duration") or 0.0,
            e.get("orig_pkts") or 0,
            e.get("resp_pkts") or 0,
            e.get("src_port") or 0,
            e.get("dst_port") or 0,
            encode(e.get("proto")),
            encode(e.get("service")),
            encode(e.get("conn_state")),
        ]
        for e in events
    ]

def extract_if(window: deque) -> list:
    """
    Extraction des features pour Isolation Forest
    Numeriques purs, fenetre des 10 derniers evenements
    """
    events = list(window)[-10:]
    return [
        [
            e.get("orig_bytes") or 0,
            e.get("resp_bytes") or 0,
            e.get("duration") or 0.0,
            e.get("orig_pkts") or 0,
            e.get("resp_pkts") or 0,
            e.get("src_port") or 0,
            e.get("dst_port") or 0,
        ]
        for e in events
    ]
