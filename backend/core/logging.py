"""
BizMind AI — Structured JSON Logging
Writes JSON-formatted logs to logs/app.log and stdout.
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from backend.core.config import get_settings


def _add_timestamp(logger: Any, method: str, event_dict: dict) -> dict:
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def _add_app_info(logger: Any, method: str, event_dict: dict) -> dict:
    event_dict["app"] = "bizmind"
    return event_dict


def setup_logging() -> None:
    """Configure structlog for JSON output to file + stdout."""
    settings = get_settings()

    logs_path = Path(settings.logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root stdlib logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)

    # File handler (rotating: 10 MB, 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        logs_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)

    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    # structlog configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            _add_timestamp,
            _add_app_info,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "bizmind") -> structlog.stdlib.BoundLogger:
    """Get a structlog bound logger."""
    return structlog.get_logger(name)
