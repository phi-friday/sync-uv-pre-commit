# sync-rye-pre-commit

## how to use
```yaml
repos:
  - hooks:
      - id: sync-rye-pre-commit
        args:
          - "-a ruff:ruff:v:"
          - "-a ruff:ruff-format:v:"
    repo: https://github.com/phi-friday/sync-rye-pre-commit
    rev: v0.1.0
```

## expected output
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