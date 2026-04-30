"""
logger.py — Logging centralizado do Job Tracker.
Substitui print() espalhado por logging estruturado com níveis configuráveis.
"""

import logging
import os
import sys

LOG_LEVEL = os.getenv("JOB_TRACKER_LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("JOB_TRACKER_LOG_FILE", "")


def get_logger(name: str) -> logging.Logger:
    """Retorna logger configurado para o módulo."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # file handler (opcional)
    if LOG_FILE:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        fh = logging.FileHandler(LOG_FILE)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.propagate = False
    return logger
