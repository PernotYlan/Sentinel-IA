import threading
import json
import time
import random
from src.worker import get_queue
from src.logger import logger

_ZEEK_TEMPLATE = {
    "tags": ["zeek"],
    "proto": "tcp",
    "service": "http",
    "conn_state": "SF",
}

_SYSLOG_TEMPLATE = {
    "tags": ["beats_input_codec_plain_applied"],
    "message": "session opened for user root by (uid=0)",
    "host": {"hostname": "sentinel-vm"},
    "process": {"name": "sshd", "pid": 1234},
}

_SRC_IPS  = ["192.168.1.10", "10.0.0.45", "172.16.0.5", "185.220.101.47"]
_DST_IPS  = ["10.0.0.1", "10.0.0.2", "10.0.0.5"]
_SERVICES = ["http", "ssh", "dns", "ftp", None]

def _make_zeek_event() -> str:
    e = dict(_ZEEK_TEMPLATE)
    e["id.orig_h"]  = random.choice(_SRC_IPS)
    e["id.resp_h"]  = random.choice(_DST_IPS)
    e["id.orig_p"]  = random.randint(1024, 65535)
    e["id.resp_p"]  = random.choice([80, 443, 22, 53, 21])
    e["service"]    = random.choice(_SERVICES)
    e["duration"]   = round(random.uniform(0.001, 5.0), 3)
    e["orig_bytes"] = random.randint(0, 50000)
    e["resp_bytes"] = random.randint(0, 50000)
    e["orig_pkts"]  = random.randint(1, 100)
    e["resp_pkts"]  = random.randint(0, 100)
    e["@timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return json.dumps(e)

def _make_syslog_event() -> str:
    e = dict(_SYSLOG_TEMPLATE)
    e["@timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return json.dumps(e)

def _producer_loop(rate: float, stop_event: threading.Event):
    """
    Genere des evenements mock a un rythme defini (evenements/seconde)
    et les pousse dans la queue partagee
    """
    # // TODO: supprimer mock_producer.py une fois le stream Redis reel disponible (2 semaines)
    interval = 1.0 / rate
    q = get_queue()
    logger.info(f"[MockProducer] Demarrage — {rate} evt/s")
    while not stop_event.is_set():
        if random.random() < 0.85:
            q.put(_make_zeek_event())
        else:
            q.put(_make_syslog_event())
        time.sleep(interval)
    logger.info("[MockProducer] Arret")

def start_mock_producer(rate: float = 5.0) -> tuple[threading.Thread, threading.Event]:
    """
    Demarre le producteur mock en arriere-plan
    rate = nombre d'evenements par seconde
    Retourne (thread, stop_event) — appeler stop_event.set() pour arreter
    """
    stop_event = threading.Event()
    t = threading.Thread(
        target=_producer_loop,
        args=(rate, stop_event),
        daemon=True,
        name="MockProducer"
    )
    t.start()
    return t, stop_event
