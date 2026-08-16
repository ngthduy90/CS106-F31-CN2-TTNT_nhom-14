"""Uniform logging for every script in the project.

Console output stays readable while a full copy goes to data/_logs/<step>.log, which is
what gets attached when a crawl or a training run has to be explained afterwards.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src import config

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
_DATEFMT = "%H:%M:%S"


def get_logger(step: str, level: int = logging.INFO) -> logging.Logger:
    """Return a logger that writes to the console and to a per-step log file."""
    logger = logging.getLogger(step)
    if logger.handlers:  # already configured in this process
        return logger

    logger.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    logger.addHandler(console)

    log_dir: Path = config.DATA / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(log_dir / f"{stamp}_{step}.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    logger.addHandler(file_handler)

    return logger
