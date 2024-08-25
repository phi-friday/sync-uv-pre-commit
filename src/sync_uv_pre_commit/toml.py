from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import toml

if TYPE_CHECKING:
    from os import PathLike

__all__ = []


def find_valid_extras(pyproject: dict[str, Any]) -> set[str]:
    project: dict[str, Any] = pyproject["project"]
    optional_dependencies: dict[str, list[str]] = project.setdefault(
        "optional-dependencies", {}
    )
    return set(optional_dependencies.keys())


def combine_dev_dependencies(
    pyproject: str | PathLike[str], destination: str | PathLike[str]
) -> tuple[str, Path, set[str]]:
    pyproject = Path(pyproject)
    destination = Path(destination)

    pyproject_obj = read_pyproject(pyproject)
    key, new_pyproject = dev_dependencies_to_dependencies(pyproject_obj)
    write_pyproject(new_pyproject, destination)
    extras = find_valid_extras(new_pyproject)

    return key, destination, extras


def read_pyproject(pyproject: str | PathLike[str]) -> dict[str, Any]:
    pyproject = Path(pyproject)
    with pyproject.open() as f:
        return toml.load(f)


def write_pyproject(
    pyproject: dict[str, Any], pyproject_path: str | PathLike[str]
) -> Path:
    pyproject_path = Path(pyproject_path)
    with pyproject_path.open("w") as f:
        toml.dump(pyproject, f)
    return pyproject_path


def dev_dependencies_to_dependencies(
    pyproject: str | PathLike[str] | dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if not isinstance(pyproject, dict):
        pyproject = read_pyproject(pyproject)

    key = "dev_dependencies"
    project: dict[str, Any] = pyproject["project"]

    optional_dependencies: dict[str, list[str]] = project.setdefault(
        "optional-dependencies", {}
    )
    if key in optional_dependencies:
        key = f"new_{key}"

    tools: dict[str, Any] = pyproject.setdefault("tool", {})
    uv_config: dict[str, Any] = tools.setdefault("uv", {})
    dev_dependencies: list[str] = uv_config.setdefault("dev-dependencies", [])

    optional_dependencies[key] = dev_dependencies
    pyproject["project"]["optional-dependencies"] = optional_dependencies

    return key, pyproject
