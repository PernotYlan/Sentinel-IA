import json
from src.db import dump_sqlite

counters = {"zeek": 0, "syslog": 0, "db": 0}

def parse_zeek(data: dict) -> dict:
    """
    fills a dic FRANCAIS OUBLIE PAS"""
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
    dump_sqlite(data)

def parsing_service_selector(raw: str):
    """
    ecrire qqch"""
    data = json.loads(raw)
    tags = data.get("tags", [])
    print(f"TAGS: {tags}")

    if "zeek" in tags:
        parse_zeek(data)
        counters["zeek"] += 1
        print(f"\033[92mAll Good Zeek [{counters['zeek']}]\033[00m")
    elif "beats_input_codec_plain_applied" in tags:
        parse_syslog(data)
        counters["syslog"] += 1
        print(f"\033[94mAll Good Syslog [{counters['syslog']}]\033[00m")
    else:
        dump_sqlite(data)
        counters["db"] += 1
        print(f"\033[93mAll Good DB [{counters['db']}]\033[00m")