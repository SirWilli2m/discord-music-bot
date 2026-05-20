import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


def _resolve_log_path() -> str:
    explicit = os.getenv("LOG_FILE")
    if explicit:
        return explicit
    logs_dir = Path("logs")
    if logs_dir.is_dir():
        return str(logs_dir / "bocchi.log")
    return "bocchi.log"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("bocchi")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = _resolve_log_path()
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


log = setup_logging()
