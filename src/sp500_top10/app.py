"""Command-line interface for the single-file runner."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import load_config
from .pipeline import STAGES, execute


def main(project_root: Path | None = None, argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and analyze concentrated S&P 500 portfolios."
    )
    parser.add_argument(
        "--stage",
        choices=list(STAGES),
        help="Run one stage; required upstream results must already exist.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use a recorded, checksummed market-data snapshot.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Project root for an installed command; relative paths resolve here.",
    )
    args = parser.parse_args(argv)
    root = args.root or project_root
    if root is None:
        parser.error("Pass --root when using the installed command outside run.py.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = load_config(root)
        context = execute(config, args.stage, args.offline)
    except Exception:
        logging.exception("Run failed; previously saved checkpoints are retained.")
        return 1
    logging.info("Complete. Run record: %s", context.path)
    return 0
