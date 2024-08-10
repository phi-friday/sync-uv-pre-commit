from __future__ import annotations

import logging
from typing import override

__all__ = []

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


class ColorFormatter(logging.Formatter):
    @override
    def formatMessage(self, record: logging.LogRecord) -> str:
        level = record.levelname.upper()
        if level in _COLORS_LEVEL:
            level = f"{_COLORS_LEVEL[level]}{level}{_RESET}"
            record.levelname = level
        return super().formatMessage(record)
