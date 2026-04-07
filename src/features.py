from collections import deque

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
