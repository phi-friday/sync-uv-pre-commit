from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from enum import IntEnum
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from pre_commit.clientlib import InvalidConfigError, load_config
from typing_extensions import NotRequired, Required

from sync_uv_pre_commit.log import ColorFormatter
from sync_uv_pre_commit.toml import find_valid_extras

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike

__all__ = []

_RE_VERSION = "{name}==(?P<version>.+)"
_UV_VERSION_MINIMA = "0.4.7"  # uv export --output-file
logger = logging.getLogger("sync_uv_pre_commit")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = ColorFormatter(fmt="[{levelname:s}] - {message:s}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Hook(TypedDict, total=True):
    id: str
    rev: str


class Args(TypedDict):
    name: Required[str]
    hook_id: Required[str]
    prefix: NotRequired[str]
    suffix: NotRequired[str]


class ExitCode(IntEnum):
    UNKNOWN = 999
    MISSING = 127
    PARSING = 1
    MISMATCH = 2
    VERSION = 3


def create_version_pattern(name: str) -> re.Pattern[str]:
    text = rf"{_RE_VERSION.format(name=name)}"
    return re.compile(text)


@lru_cache
def resolve_pyproject(
    *,
    pyproject: str | PathLike[str],
    temp_directory: str | PathLike[str],
    extras: tuple[str, ...],
    no_dev: bool,
) -> Path:
    origin_pyproject, temp_directory = Path(pyproject), Path(temp_directory)
    new_pyproject = temp_directory / "pyproject.toml"
    requirements = temp_directory / "requirements.txt"

    shutil.copy(origin_pyproject, new_pyproject)
    valid_extras = find_valid_extras(new_pyproject)

    command = ["uv", "export", "--no-hashes", f"--output-file={requirements!s}"]
    extras = tuple(extra for extra in extras if extra in valid_extras)
    if extras:
        command.extend(chain.from_iterable(("--extra", extra) for extra in extras))
    if no_dev:
        command.append("--no-dev")

    logger.info("Running command:\n    %s", " ".join(command))

    uv_process = subprocess.run(  # noqa: S603
        command, cwd=temp_directory, check=False, capture_output=True, text=True
    )
    try:
        uv_process.check_returncode()
    except subprocess.CalledProcessError as exc:
        logger.error("uv lock failed: %s", exc.stderr)  # noqa: TRY400
        if exc.returncode == ExitCode.MISSING.value:
            sys.exit(ExitCode.MISSING)
        if exc.returncode == ExitCode.PARSING.value:
            sys.exit(ExitCode.PARSING)
        sys.exit(ExitCode.UNKNOWN)

    return requirements


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
        logger.error("Package %s not found in lock file", name)
        sys.exit(ExitCode.PARSING)

    return match.group("version")


def find_version_in_pyproject(
    *,
    name: str,
    pyproject: str | PathLike[str],
    temp_directory: str | PathLike[str],
    extras: tuple[str, ...],
    no_dev: bool,
) -> str:
    lock_file = resolve_pyproject(
        pyproject=pyproject, temp_directory=temp_directory, extras=extras, no_dev=no_dev
    )
    return find_version(name, lock_file)


@lru_cache
def resolve_pre_commit(pre_commit: str | PathLike[str]) -> dict[str, str]:
    try:
        config = load_config(pre_commit)
    except InvalidConfigError:
        logger.critical("Failed to load pre-commit config")
        sys.exit(ExitCode.PARSING)

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
    args = arg_string.strip().split(":")
    size = len(args)

    if size == 1:
        return Args(name=args[0], hook_id=args[0])
    if size == 2:  # noqa: PLR2004
        return Args(name=args[0], hook_id=args[1])
    if size == 3:  # noqa: PLR2004
        return Args(name=args[0], hook_id=args[1], prefix=args[2])
    return Args(name=args[0], hook_id=args[1], prefix=args[2], suffix=args[3])


def process(
    *,
    args: list[Args],
    pyproject: str | PathLike[str],
    pre_commit: str | PathLike[str],
    extras: tuple[str, ...],
    no_dev: bool,
) -> None:
    if args:
        logger.info("Processing args:")
        for arg in args:
            logger.info(" - `%s`", arg)
    logger.info("Processing pyproject: `%s`", pyproject)
    logger.info("Processing pre_commit: `%s`", pre_commit)

    hooks = resolve_pre_commit(pre_commit)
    errors: list[tuple[str, str, str, str] | None] = [None] * len(args)
    with tempfile.TemporaryDirectory() as temp_directory:
        for index, arg in enumerate(args):
            version = find_version_in_pyproject(
                name=arg["name"],
                pyproject=pyproject,
                temp_directory=temp_directory,
                extras=extras,
                no_dev=no_dev,
            )
            version = f"{arg.get('prefix', '')}{version}{arg.get('suffix', '')}"

            if hooks[arg["hook_id"]] == version:
                logger.info(
                    "Expected %s to be %s, and found %s",
                    arg["hook_id"],
                    version,
                    hooks[arg["hook_id"]],
                )
                continue

            errors[index] = (
                "Expected %s to be %s, but found %s",
                arg["hook_id"],
                version,
                hooks[arg["hook_id"]],
            )

    non_null_errors = [error for error in errors if error]
    args_count = len(args)
    error_count = len(non_null_errors)
    success_count = args_count - error_count
    level = logging.ERROR if error_count else logging.INFO

    logger.log(level, "Results:: %d success, %d errors", success_count, error_count)
    if error_count:
        for error in non_null_errors:
            logger.error(*error)
        sys.exit(ExitCode.MISMATCH)


def check_uv_version() -> None:
    command = ["uv", "--version"]
    process = subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603

    try:
        process.check_returncode()
    except subprocess.CalledProcessError as exc:
        logger.error("uv version failed: %s", exc.stderr)  # noqa: TRY400
        if exc.returncode == ExitCode.MISSING.value:
            sys.exit(ExitCode.MISSING)
        if exc.returncode == ExitCode.PARSING.value:
            sys.exit(ExitCode.PARSING)
        sys.exit(ExitCode.UNKNOWN)

    version = process.stdout.strip().split()[1]
    logger.info("uv version: %s", version)

    if version < _UV_VERSION_MINIMA:
        logger.critical("uv version %s is not supported", version)
        sys.exit(ExitCode.VERSION)


def _main() -> None:
    from importlib.metadata import version

    check_uv_version()

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", action="append", default=[])
    parser.add_argument("-p", "--pyproject", type=str, default="pyproject.toml")
    parser.add_argument(
        "-P", "--pre-commit", type=str, default=".pre-commit-config.yaml"
    )
    parser.add_argument("-l", "--log-level", type=str, default="INFO")
    parser.add_argument("-e", "--extra", action="append", default=[])
    parser.add_argument("--no-dev", action="store_true", default=False)
    parser.add_argument("dummy", nargs="*")

    args = parser.parse_args()
    args_string: list[str] = args.args
    version_args = [resolve_arg(arg) for arg in args_string]
    pyproject, pre_commit, extras, no_dev = (
        args.pyproject,
        args.pre_commit,
        args.extra,
        args.no_dev,
    )
    logger.setLevel(args.log_level)

    pre_commit_version = version("pre-commit")
    logger.debug("python version: %s", sys.version)
    logger.debug("pre-commit version: %s", pre_commit_version)

    process(
        args=version_args,
        pyproject=pyproject,
        pre_commit=pre_commit,
        extras=tuple(extras),
        no_dev=no_dev,
    )


def main() -> None:
    try:
        _main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        logger.critical("Unexpected error:: %s, %s", type(exc), exc, stack_info=True)
        sys.exit(ExitCode.UNKNOWN)
