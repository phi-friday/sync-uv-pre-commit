from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit

if TYPE_CHECKING:
    from os import PathLike

__all__ = []


def find_valid_extras(pyproject: dict[str, Any]) -> set[str]:
    project: dict[str, Any] = pyproject["project"]
    optional_dependencies: dict[str, list[str]] = project.get(
        "optional-dependencies", {}
    )
    return set(optional_dependencies.keys())


def find_valid_groups(pyproject: dict[str, Any]) -> set[str]:
    dependency_groups = pyproject.get("dependency-groups", {})
    return set(dependency_groups.keys())


def read_pyproject(pyproject: str | PathLike[str]) -> dict[str, Any]:
    pyproject = Path(pyproject)
    with pyproject.open("rb") as f:
        return tomlkit.load(f)


def write_pyproject(
    pyproject: dict[str, Any], pyproject_path: str | PathLike[str]
) -> Path:
    pyproject_path = Path(pyproject_path)
    with pyproject_path.open("w") as f:
        tomlkit.dump(pyproject, f)
    return pyproject_path


def remove_dynamic_version(pyproject: dict[str, Any]) -> dict[str, Any]:
    project: dict[str, Any] = pyproject["project"]
    if "dynamic" not in project:
        return pyproject

    dynamic: list[str] = project["dynamic"]
    if "version" not in dynamic:
        return pyproject

    pyproject = deepcopy(pyproject)
    pyproject["project"]["dynamic"].remove("version")
    pyproject["project"]["version"] = "0.1.0"
    return pyproject
