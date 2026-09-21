"""Run the application from a checkout, including after moving the folder."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

if __name__ == "__main__":
    from sp500_top10.app import main

    raise SystemExit(main(project_root=PROJECT_ROOT))
