"""Preserve a private reference before migration; never modify the source."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = root / ".private/reference"
    if destination.exists():
        raise SystemExit("Reference already exists; refusing to overwrite it.")
    source = args.source.resolve(strict=True)
    if Path(str(source) + ".wal").exists():
        raise SystemExit("Close the database writer before freezing its reference.")
    original_hash = sha256(source)
    destination.mkdir(parents=True)
    shutil.copy2(source, destination / "reference.duckdb")
    if sha256(destination / "reference.duckdb") != original_hash or sha256(source) != original_hash:
        raise RuntimeError("Source changed while copying; reference is not valid.")
    notebooks = {}
    for notebook in root.glob("*.ipynb"):
        notebooks[notebook.name] = sha256(notebook)
        (destination / "notebooks").mkdir(exist_ok=True)
        shutil.copy2(notebook, destination / "notebooks" / notebook.name)
    exports = {}
    for group in ["analytics", "factor_attribution"]:
        for path in sorted((args.outputs / group).glob("*.csv")):
            target = destination / "outputs" / group / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = csv.reader(stream)
                columns = next(rows)
                row_count = sum(1 for _ in rows)
            exports[f"{group}/{path.name}"] = {
                "sha256": sha256(path),
                "columns": columns,
                "rows": row_count,
            }
    manifest = {
        "source_sha256": original_hash,
        "source_bytes": source.stat().st_size,
        "python": sys.version,
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "notebooks": notebooks,
        "csvs": exports,
        "status": "frozen candidate; equivalence must be verified",
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"Reference saved: {len(notebooks)} notebooks, {len(exports)} CSVs, database hash verified."
    )


if __name__ == "__main__":
    main()
