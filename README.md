# sync-rye-pre-commit
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!CAUTION]
> Migrate from `rye` to `uv`.
> 
> see more: https://github.com/astral-sh/rye/discussions/1342

## how to use
```yaml
repos:
  - hooks:
      - id: sync-rye-pre-commit
        args:
          - "-a ruff:ruff:v:"
          - "-a ruff:ruff-format:v:"
    repo: https://github.com/phi-friday/sync-rye-pre-commit
    rev: v0.1.4
```

### args
- `-a` or `--args`: `{library}[:{hook_id}[:{prefix}[:{suffix}]]]` (defaults: `[]`)
- `-p` or `--pyproject`: `pyproject.toml` path (defaults: `pyproject.toml`)
- `-P` or `--pre-commit`: `.pre-commit-config.yaml` path (defaults: `.pre-commit-config.yaml`)
- `-l` or `--log-level`: log level (defaults: `INFO`)

## success output
```bash
❯ rye run pre-commit run --all-files --show-diff-on-failure --verbose
Sync rye and pre commit..................................................Passed
- hook id: sync-rye-pre-commit
- duration: 0.53s

[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'mypy', 'hook_id': 'mypy', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Expected ruff to be v0.5.7, and found v0.5.7
[INFO] - Expected ruff-format to be v0.5.7, and found v0.5.7
[INFO] - Expected mypy to be v1.11.1, and found v1.11.1
[INFO] - Results:: 3 success, 0 errors
```

## error output
```bash
❯ rye run pre-commit run --all-files --show-diff-on-failure --verbose
Sync rye and pre commit..................................................Failed
- hook id: sync-rye-pre-commit
- duration: 0.13s
- exit code: 1

[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'mypy', 'hook_id': 'mypy', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Expected mypy to be v1.11.1, and found v1.11.1
[ERROR] - Results:: 1 success, 2 errors
[ERROR] - Expected ruff to be v0.5.7, but found v0.5.6
[ERROR] - Expected ruff-format to be v0.5.7, but found v0.5.6
```