import json

def parse_zeek():
    print("nuh uh")

def parse_syslog():
    print("nuh uh")

def dump_sqlite():
    print("nuh uh")

def parsing_service_selector(raw: str):
    data = json.loads(raw)
    tags = data.get("tags", [])

    if "zeek" in tags:
        parse_zeek(data)
    elif "beats_input_codec_plain_applied" in tags:
        parse_syslog(data)
    else:
        dump_sqlite(data)