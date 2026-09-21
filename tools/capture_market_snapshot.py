"""Record existing provider tables for explicit offline reproduction."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sp500_top10.config import load_config
from sp500_top10.market_data.snapshot import capture_database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(ROOT)
    capture_database(
        args.source.resolve(strict=True),
        config.paths.cache / "market_data",
        config.market_data,
    )
    print("Checksummed normalized market-data snapshot saved. Source unchanged.")
