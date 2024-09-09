from __future__ import annotations

import logging
from enum import IntEnum
from typing import Any

from typing_extensions import override

__all__ = []

logger: logging.Logger

_COLORS_INT = {"red": 31, "green": 32, "yellow": 33, "cyan": 36}
_COLORS = {key: f"\x1b[{index};20m" for key, index in _COLORS_INT.items()}
_COLORS_LEVEL = {
    "DEBUG": _COLORS["cyan"],
    "INFO": _COLORS["green"],
    "WARNING": _COLORS["yellow"],
    "ERROR": _COLORS["red"],
    "CRITICAL": _COLORS["red"],
}
_RESET = "\x1b[0m"


class ExitCode(IntEnum):
    UNKNOWN = 999
    MISSING = 127
    PARSING = 1
    MISMATCH = 2
    VERSION = 3


class ColorFormatter(logging.Formatter):
    @override
    def formatMessage(self, record: logging.LogRecord) -> str:
        level = record.levelname.upper()
        if level in _COLORS_LEVEL:
            level = f"{_COLORS_LEVEL[level]}{level}{_RESET}"
            record.levelname = level
        return super().formatMessage(record)


def __getattr__(name: str) -> Any:
    if name == "logger":
        logger = logging.getLogger("sync_uv_pre_commit")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = ColorFormatter(fmt="[{levelname:s}] - {message:s}", style="{")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        globals()["logger"] = logger

        return logger
    error_msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(error_msg)
