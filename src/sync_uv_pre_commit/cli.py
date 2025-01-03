from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
import tempfile
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from packaging.specifiers import Specifier, SpecifierSet
from pre_commit.clientlib import InvalidConfigError, load_config
from typing_extensions import NotRequired, Required

from sync_uv_pre_commit.log import ExitCode, logger
from sync_uv_pre_commit.package import find_specifier, parse_lockfile
from sync_uv_pre_commit.toml import (
    find_valid_extras,
    find_valid_groups,
    read_pyproject,
    remove_dynamic_version,
    write_pyproject,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike


__all__ = []

_UV_VERSION_MINIMA = Specifier(">=0.4.7")


class Hook(TypedDict, total=True):
    id: str
    rev: str


class Args(TypedDict):
    name: Required[str]
    hook_id: Required[str]
    prefix: NotRequired[str]
    suffix: NotRequired[str]


def resolve_pyproject(
    *,
    pyproject: str | PathLike[str],
    temp_directory: str | PathLike[str],
    extras: tuple[str, ...],
    groups: tuple[str, ...],
    no_dev: bool,
) -> Path:
    pyproject, temp_directory = Path(pyproject), Path(temp_directory)
    requirements_path = temp_directory / "requirements.txt"
    new_pyproject = temp_directory / "pyproject.toml"

    shutil.copy(pyproject, new_pyproject)
    pyproject_dict = read_pyproject(new_pyproject)
    pyproject_dict = remove_dynamic_version(pyproject_dict)
    new_pyproject.unlink()
    write_pyproject(pyproject_dict, new_pyproject)

    logger.debug("before validate extras: %s", extras)
    valid_extras = find_valid_extras(pyproject_dict)
    logger.debug("valid extras: %s", valid_extras)
    logger.debug("before validate groups: %s", groups)
    valid_groups = find_valid_groups(pyproject_dict)
    logger.debug("valid groups: %s", valid_groups)

    command = [
        "uv",
        "export",
        "--no-header",
        "--no-editable",
        "--no-hashes",
        "--no-emit-project",
        "--no-emit-workspace",
        "-o",
        str(requirements_path),
    ]
    extras = tuple(ext for extra in extras if (ext := extra.strip()) in valid_extras)
    logger.debug("extras: %s", extras)
    groups = tuple(grp for group in groups if (grp := group.strip()) in valid_groups)
    logger.debug("groups: %s", groups)
    if extras:
        command.extend(chain.from_iterable(("--extra", extra) for extra in extras))
    if groups:
        command.extend(chain.from_iterable(("--group", group) for group in groups))
    if no_dev:
        command.append("--no-dev")

    logger.info("Running command:\n    %s", " ".join(command))

    uv_process = subprocess.run(  # noqa: S603
        command, cwd=temp_directory, check=False, capture_output=True, text=True
    )
    try:
        uv_process.check_returncode()
    except subprocess.CalledProcessError as exc:
        logger.error("uv lock failed: %s", exc.stderr)
        if exc.returncode == ExitCode.MISSING.value:
            sys.exit(ExitCode.MISSING)
        if exc.returncode == ExitCode.PARSING.value:
            sys.exit(ExitCode.PARSING)
        sys.exit(ExitCode.UNKNOWN)

    return requirements_path


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


def process(  # noqa: PLR0913
    *,
    args: list[Args],
    pyproject: str | PathLike[str],
    pre_commit: str | PathLike[str],
    extras: tuple[str, ...],
    groups: tuple[str, ...],
    no_dev: bool,
) -> None:
    if args:
        logger.info("Processing args:")
        for arg in args:
            logger.info(" - `%s`", arg)
    pyproject = Path(pyproject).resolve()
    logger.info("Processing pyproject: `%s`", pyproject)
    logger.info("Processing pre_commit: `%s`", pre_commit)

    hooks = resolve_pre_commit(pre_commit)
    errors: list[tuple[str, str, SpecifierSet, str] | None] = [None] * len(args)
    with tempfile.TemporaryDirectory() as temp_directory:
        lock_file = resolve_pyproject(
            pyproject=pyproject,
            temp_directory=temp_directory,
            extras=extras,
            groups=groups,
            no_dev=no_dev,
        )
        lock = parse_lockfile(lock_file)

        for index, arg in enumerate(args):
            specifier = find_specifier(name=arg["name"], lock=lock)
            hook_rev = hooks[arg["hook_id"]]

            prefix, suffix = arg.get("prefix", ""), arg.get("suffix", "")
            if prefix and hook_rev.startswith(prefix):  # FIXME: python3.9+
                hook_rev = hook_rev[len(prefix) :]
            if suffix and hook_rev.endswith(suffix):
                hook_rev = hook_rev[: -len(suffix)]

            if specifier.contains(hook_rev):
                logger.info(
                    "Expected %s to be %s, and found %s",
                    arg["hook_id"],
                    specifier,
                    hooks[arg["hook_id"]],
                )
                continue

            errors[index] = (
                "Expected %s to be %s, but found %s",
                arg["hook_id"],
                specifier,
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
        logger.error("uv version failed: %s", exc.stderr)
        if exc.returncode == ExitCode.MISSING.value:
            sys.exit(ExitCode.MISSING)
        if exc.returncode == ExitCode.PARSING.value:
            sys.exit(ExitCode.PARSING)
        sys.exit(ExitCode.UNKNOWN)

    version = process.stdout.strip().split()[1]
    logger.info("uv version: %s", version)

    if not _UV_VERSION_MINIMA.contains(version):
        logger.critical("uv version %s is not supported", version)
        logger.critical("uv version must be %s", _UV_VERSION_MINIMA)
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
    parser.add_argument("-g", "--group", action="append", default=[])
    parser.add_argument("--no-dev", action="store_true", default=False)
    parser.add_argument("dummy", nargs="*")

    args = parser.parse_args()
    args_string: list[str] = args.args
    version_args = [resolve_arg(arg) for arg in args_string]
    pyproject, pre_commit, extras, groups, no_dev = (
        args.pyproject,
        args.pre_commit,
        args.extra,
        args.group,
        args.no_dev,
    )

    log_level = str(args.log_level).strip()
    if log_level.isdigit():
        log_level = int(log_level)
    logger.setLevel(log_level)

    pre_commit_version = version("pre-commit")
    logger.debug("python version: %s", sys.version)
    logger.debug("pre-commit version: %s", pre_commit_version)

    process(
        args=version_args,
        pyproject=pyproject,
        pre_commit=pre_commit,
        extras=tuple(extras),
        groups=tuple(groups),
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
