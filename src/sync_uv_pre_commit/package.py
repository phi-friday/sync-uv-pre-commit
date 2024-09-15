from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.requirements import Requirement

from sync_uv_pre_commit.log import ExitCode, logger

if TYPE_CHECKING:
    from os import PathLike

    from packaging.specifiers import SpecifierSet

__all__ = []


def parse_lockfile(lock_file: str | PathLike[str]) -> dict[str, Requirement]:
    lock_file = Path(lock_file)
    with lock_file.open() as file:
        return {
            (req := Requirement(line)).name: req
            for _line in file.readlines()
            if (line := _line.strip()) and not line.startswith(("#", "-e"))
        }


def find_specifier(name: str, lock: dict[str, Requirement]) -> SpecifierSet:
    reqirement = lock.get(name)

    if reqirement is None:
        logger.error("Package %s not found in lock file", name)
        sys.exit(ExitCode.PARSING)

    return reqirement.specifier
