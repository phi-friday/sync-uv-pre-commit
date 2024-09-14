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
    rev: v0.4.2
```

### args
- `-a` or `--args`: `{library}[:{hook_id}[:{prefix}[:{suffix}]]]` (defaults: `[]`)
- `-p` or `--pyproject`: `pyproject.toml` path (defaults: `pyproject.toml`)
- `-P` or `--pre-commit`: `.pre-commit-config.yaml` path (defaults: `.pre-commit-config.yaml`)
- `-l` or `--log-level`: log level (defaults: `INFO`)
- `-e` or `--extra`: optional dependencies (defaults: `[]`)
- `--no-dev`: omit uv dev dependencies

## success output
```bash
❯ uv run pre-commit run --all-files --show-diff-on-failure --verbose

Sync uv and pre commit...................................................Passed
- hook id: sync-uv-pre-commit
- duration: 0.08s

[INFO] - uv version: 0.4.7
[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Running command:
    uv export --no-hashes --output-file=/var/folders/_4/h6jc_2cs6kq7l4k8_yj7171w0000gn/T/tmprh7hmc9l/requirements.txt
[INFO] - Expected ruff to be ==0.6.4, and found v0.6.4
[INFO] - Expected ruff-format to be ==0.6.4, and found v0.6.4
[INFO] - Results:: 2 success, 0 errors
```

## error output
```bash
❯ uv run pre-commit run --all-files --show-diff-on-failure --verbose

Sync uv and pre commit...................................................Failed
- hook id: sync-uv-pre-commit
- duration: 0.08s
- exit code: 2

[INFO] - uv version: 0.4.7
[INFO] - Processing args:
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}`
[INFO] -  - `{'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}`
[INFO] - Processing pyproject: `pyproject.toml`
[INFO] - Processing pre_commit: `.pre-commit-config.yaml`
[INFO] - Running command:
    uv export --no-hashes --output-file=/var/folders/_4/h6jc_2cs6kq7l4k8_yj7171w0000gn/T/tmpk6vgib_d/requirements.txt
[ERROR] - Results:: 0 success, 2 errors
[ERROR] - Expected ruff to be ==0.6.4, but found v0.6.3
[ERROR] - Expected ruff-format to be ==0.6.4, but found v0.6.3
```