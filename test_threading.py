#!/usr/bin/env python3
"""
Test du pipeline threadé avec données mock
Lance 3 workers + 1 producteur mock pendant 10 secondes
"""
import time
from src.db import init_db
from src.worker import start_workers, stop_workers
from src.mock_producer import start_mock_producer

N_WORKERS = 3
DURATION  = 10  # secondes
RATE      = 800.0 # evenements/seconde

if __name__ == "__main__":
    init_db()
    start_workers(N_WORKERS)
    _, stop_event = start_mock_producer(rate=RATE)

    print(f"Test en cours pendant {DURATION}s ({RATE} evt/s, {N_WORKERS} workers)...")
    time.sleep(DURATION)

    stop_event.set()
    stop_workers(N_WORKERS)
    print("Test termine.")
