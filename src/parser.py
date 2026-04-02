def parsing_service_selector(raw: str):
    if "zeek" in raw:
        print("zeek parser")
    if "syslog" in raw:
        print("syslog parser")
    else:
        print("SQLite")
