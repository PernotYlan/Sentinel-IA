import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv(".env")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE  = os.getenv("LOG_FILE", "/app/sentinel.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)-12s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("sentinel")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Handler stdout
_stream = logging.StreamHandler()
_stream.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
logger.addHandler(_stream)

# Handler fichier rotatif
try:
    _file = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5)
    _file.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(_file)
except (OSError, PermissionError):
    # Hors Docker le chemin /app n'existe pas dcp on log sur stdout
    pass
