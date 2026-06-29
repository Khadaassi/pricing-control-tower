import json
import logging
from datetime import UTC, datetime
from typing import Any

SERVICE_NAME = "ai_service"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": logging.getLevelName(level),
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }

    logger.log(level, json.dumps(payload, ensure_ascii=False))
