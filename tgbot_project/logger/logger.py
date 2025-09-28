"""Project-wide logging helpers."""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from ..config import config_logger

_LOG_ROOT = Path(config_logger.log_file).parent


def _ensure_log_dir() -> None:
    if not _LOG_ROOT.exists():
        _LOG_ROOT.mkdir(parents=True, exist_ok=True)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger instance."""
    logger = logging.getLogger(name)

    if getattr(logger, "_chiffon_logger_configured", False):
        return logger

    level = getattr(logging, config_logger.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(config_logger.formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _ensure_log_dir()
    log_file = Path(config_logger.log_file)
    rotate_conf = getattr(config_logger, "rotate", None)
    max_bytes = getattr(rotate_conf, "max_bytes", 5 * 1024 * 1024)
    backup_count = getattr(rotate_conf, "backup_count", 3)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger._chiffon_logger_configured = True  # type: ignore[attr-defined]
    return logger

