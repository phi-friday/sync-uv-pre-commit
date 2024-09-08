from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import toml

if TYPE_CHECKING:
    from os import PathLike

__all__ = []


@lru_cache
def find_valid_extras(pyproject: str | PathLike[str] | dict[str, Any]) -> set[str]:
    if not isinstance(pyproject, dict):
        pyproject = read_pyproject(pyproject)

    project: dict[str, Any] = pyproject["project"]
    optional_dependencies: dict[str, list[str]] = project.setdefault(
        "optional-dependencies", {}
    )
    return set(optional_dependencies.keys())


@lru_cache
def read_pyproject(pyproject: str | PathLike[str]) -> dict[str, Any]:
    pyproject = Path(pyproject)
    with pyproject.open() as f:
        return toml.load(f)
