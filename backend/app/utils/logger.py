"""Structured logging for Vedang backend."""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")


def setup_logger(name: str = "vedang", level: int = logging.DEBUG) -> logging.Logger:
    """Create a logger with console + rotating file output."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    detailed = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    simple = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")

    # File handler — rotated at 5 MB, keep 3 backups
    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{datetime.now():%Y-%m-%d}.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(detailed)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(simple)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def get_logger(name: str = "vedang") -> logging.Logger:
    """Get or create a named logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
