from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, NotRequired, Required, TypedDict

from pre_commit.clientlib import load_config

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike

__all__ = []

_RE_VERSION = "{name}==(?P<version>.+)"


class Hook(TypedDict, total=True):
    id: str
    rev: str


class Args(TypedDict):
    name: Required[str]
    hook_id: Required[str]
    prefix: NotRequired[str]
    suffix: NotRequired[str]


def create_version_pattern(name: str) -> re.Pattern[str]:
    text = rf"{_RE_VERSION.format(name=name)}"
    return re.compile(text)


@lru_cache
def resolve_pyproject(
    pyproject: str | PathLike[str], temp_directory: str | PathLike[str]
) -> Path:
    origin_pyproject, temp_directory = Path(pyproject), Path(temp_directory)
    new_pyproject = temp_directory / "pyproject.toml"
    shutil.copy(origin_pyproject, new_pyproject)

    subprocess.run(["rye", "lock"], cwd=temp_directory, check=True)  # noqa: S603, S607
    shutil.rmtree(temp_directory / ".venv")
    return temp_directory / "requirements-dev.lock"


@lru_cache
def load_lockfile(lock_file: str | PathLike[str]) -> str:
    lock_file = Path(lock_file)
    with lock_file.open() as f:
        return f.read()


def find_version(name: str, lock_file: str | PathLike[str]) -> str:
    pattern = create_version_pattern(name)
    lock = load_lockfile(lock_file)

    match = pattern.search(lock)
    if match is None:
        error_msg = f"Package {name} not found in lock file"
        raise ValueError(error_msg)

    return match.group("version")


def find_version_in_pyproject(
    name: str, pyproject: str | PathLike[str], temp_directory: str | PathLike[str]
) -> str:
    lock_file = resolve_pyproject(pyproject, temp_directory)
    return find_version(name, lock_file)


@lru_cache
def resolve_pre_commit(pre_commit: str | PathLike[str]) -> dict[str, str]:
    config = load_config(pre_commit)
    repos = config["repos"]
    return {hook["id"]: hook["rev"] for hook in resolve_hook(repos)}


def resolve_hook(repos: list[dict[str, Any]]) -> Generator[Hook, None, None]:
    hook: dict[str, Any]
    for hooks in repos:
        if "rev" not in hooks:
            continue

        for hook in hooks["hooks"]:
            yield Hook(id=hook["id"], rev=hooks["rev"])


def resolve_arg(arg_string: str) -> Args:
    args = arg_string.split(":")
    size = len(args)

    if size == 1:
        return Args(name=args[0], hook_id=args[0])
    if size == 2:  # noqa: PLR2004
        return Args(name=args[0], hook_id=args[1])
    if size == 3:  # noqa: PLR2004
        return Args(name=args[0], hook_id=args[1], prefix=args[2])
    return Args(name=args[0], hook_id=args[1], prefix=args[2], suffix=args[3])


def process(
    args: list[Args], pyproject: str | PathLike[str], pre_commit: str | PathLike[str]
) -> None:
    hooks = resolve_pre_commit(pre_commit)
    with tempfile.TemporaryDirectory() as temp_directory:
        for arg in args:
            version = find_version_in_pyproject(arg["name"], pyproject, temp_directory)
            version = f"{arg.get("prefix", "")}{version}{arg.get("suffix", "")}"

            if hooks[arg["hook_id"]] != version:
                error_msg = (
                    f"Expected {arg["hook_id"]} to be {version}, "
                    f"but found {hooks[arg["hook_id"]]}"
                )
                raise ValueError(error_msg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", nargs="+", default=[])
    parser.add_argument("-p", "--pyproject", type=str, default="pyproject.toml")
    parser.add_argument(
        "-P", "--pre-commit", type=str, default=".pre-commit-config.yaml"
    )

    args = parser.parse_args()
    args_string: list[str] = args.args
    version_args = [resolve_arg(arg) for arg in args_string]
    pyproject, pre_commit = args.pyproject, args.pre_commit

    process(version_args, pyproject, pre_commit)
