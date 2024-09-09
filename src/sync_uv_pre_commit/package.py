from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.requirements import Requirement

from sync_uv_pre_commit.log import ExitCode, logger

if TYPE_CHECKING:
    from os import PathLike

    from packaging.specifiers import SpecifierSet

__all__ = []


@lru_cache
def parse_lockfile(lock_file: str | PathLike[str]) -> dict[str, Requirement]:
    lock_file = Path(lock_file)
    with lock_file.open() as file:
        return {
            (req := Requirement(line.strip())).name: req for line in file.readlines()
        }


def find_specifier(name: str, lock_file: str | PathLike[str]) -> SpecifierSet:
    lock = parse_lockfile(lock_file)
    reqirement = lock.get(name)

    if reqirement is None:
        logger.error("Package %s not found in lock file", name)
        sys.exit(ExitCode.PARSING)

    return reqirement.specifier
