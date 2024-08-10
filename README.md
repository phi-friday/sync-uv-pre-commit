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
$ pre-commit run --all-files --show-diff-on-failure --verbose
[INFO] Initializing environment for https://github.com/phi-friday/sync-rye-pre-commit.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
Sync rye and pre commit..................................................Passed
- hook id: sync-rye-pre-commit
- duration: 0.34s

Processing args: "[{'name': 'ruff', 'hook_id': 'ruff', 'prefix': 'v', 'suffix': ''}, {'name': 'ruff', 'hook_id': 'ruff-format', 'prefix': 'v', 'suffix': ''}]"
Processing pyproject: "pyproject.toml"
Processing pre_commit: ".pre-commit-config.yaml"
Expected ruff to be v0.5.7, and found v0.5.7
Expected ruff-format to be v0.5.7, and found v0.5.7
```