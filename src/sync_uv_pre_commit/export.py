from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent
sys.path.append(str(WORKSPACE / "src"))


if __name__ == "__main__":
    from sync_uv_pre_commit.cli import main

    main()
