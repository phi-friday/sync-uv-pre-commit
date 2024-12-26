# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "packaging",
#     "pre-commit>=3.5.0",
#     "tomlkit>=0.13.2",
#     "typing-extensions>=4.12.2",
# ]
# ///

from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent
sys.path.append(str(WORKSPACE / "src"))


if __name__ == "__main__":
    from sync_uv_pre_commit.cli import main

    main()
