# sync-uv-pre-commit
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## how to use
```yaml
repos:
  - hooks:
      - id: sync-uv-pre-commit
        args:
          - "-a ruff:ruff:v:"
          - "-a ruff:ruff-format:v:"
          - "-e some_extra"
    repo: https://github.com/phi-friday/sync-uv-pre-commit
    rev: v0.1.2
```

### args
- `-a` or `--args`: `{library}[:{hook_id}[:{prefix}[:{suffix}]]]` (defaults: `[]`)
- `-p` or `--pyproject`: `pyproject.toml` path (defaults: `pyproject.toml`)
- `-P` or `--pre-commit`: `.pre-commit-config.yaml` path (defaults: `.pre-commit-config.yaml`)
- `-l` or `--log-level`: log level (defaults: `INFO`)
- `-e` or `--extra`: optional dependencies (defaults: `[]`)

## success output
```bash
❯ uv run pre-commit run --all-files --show-diff-on-failure --verbose
Sync uv and pre commit..................................................Passed
- hook id: sync-uv-pre-commit
- duration: 0.53s

[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'mypy', 'hook_id': 'mypy', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Running command:
    uv pip compile pyproject.toml -o requirements.txt --extra dev_dependencies
[INFO] - Expected ruff to be v0.5.7, and found v0.5.7
[INFO] - Expected ruff-format to be v0.5.7, and found v0.5.7
[INFO] - Expected mypy to be v1.11.1, and found v1.11.1
[INFO] - Results:: 3 success, 0 errors
```

## error output
```bash
❯ uv run pre-commit run --all-files --show-diff-on-failure --verbose
Sync uv and pre commit..................................................Failed
- hook id: sync-uv-pre-commit
- duration: 0.13s
- exit code: 1

[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'mypy', 'hook_id': 'mypy', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Running command:
    uv pip compile pyproject.toml -o requirements.txt --extra dev_dependencies
[INFO] - Expected mypy to be v1.11.1, and found v1.11.1
[ERROR] - Results:: 1 success, 2 errors
[ERROR] - Expected ruff to be v0.5.7, but found v0.5.6
[ERROR] - Expected ruff-format to be v0.5.7, but found v0.5.6
```