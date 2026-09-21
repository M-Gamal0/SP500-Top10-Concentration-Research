"""Compare saved production outputs against the private frozen reference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sp500_top10.config import load_config
from sp500_top10.data.database import identifier
from sp500_top10.reporting.catalog import CATALOG
from sp500_top10.run_context import digest_file, save_json


def verify(stage, config, reference):
    report = {"stage": stage, "tables": {}, "csvs": {}}
    with (
        duckdb.connect(str(reference / "reference.duckdb"), read_only=True) as expected,
        duckdb.connect(str(config.paths.results), read_only=True) as actual,
    ):
        for table in CATALOG[stage]["tables"]:
            query = f"SELECT * FROM {identifier(table)} ORDER BY ALL"
            left = expected.execute(query).df()
            right = actual.execute(query).df()
            left_schema = expected.execute(f"DESCRIBE {identifier(table)}").fetchall()
            right_schema = actual.execute(f"DESCRIBE {identifier(table)}").fetchall()
            if left_schema != right_schema:
                raise AssertionError(
                    f"{table}: database schema differs\n{left_schema}\n{right_schema}"
                )
            pd.testing.assert_frame_equal(
                left, right, check_exact=False, rtol=1e-12, atol=1e-12, obj=table
            )
            report["tables"][table] = {
                "rows": len(left),
                "status": "matched",
                "absolute_tolerance": 1e-12,
                "relative_tolerance": 1e-12,
            }
    group = "factor_attribution" if stage == "factor-attribution" else "analytics"
    for filename in CATALOG[stage]["csvs"]:
        original = reference / "outputs" / group / filename
        result = config.paths.outputs / group / filename
        left = pd.read_csv(original, keep_default_na=False)
        right = pd.read_csv(result, keep_default_na=False)
        pd.testing.assert_frame_equal(
            left, right, check_exact=False, rtol=1e-12, atol=1e-12, obj=filename
        )
        report["csvs"][filename] = {
            "rows": len(left),
            "status": "matched",
            "byte_identical": digest_file(original) == digest_file(result),
        }
    manifest = json.loads((reference / "manifest.json").read_text(encoding="utf-8"))
    if digest_file(config.paths.source) != manifest["source_sha256"]:
        raise AssertionError("Original source changed since baseline capture.")
    for name, digest in manifest["notebooks"].items():
        if digest_file(ROOT / name) != digest:
            raise AssertionError(f"Original notebook changed: {name}")
    save_json(ROOT / ".private/verification" / f"{stage}.json", report)
    print(
        f"PASS {stage}: {len(report['tables'])} tables, {len(report['csvs'])} CSVs; originals unchanged."
    )
    if report["csvs"]:
        print(
            "Byte-identical CSVs:",
            sum(v["byte_identical"] for v in report["csvs"].values()),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=list(CATALOG))
    parser.add_argument("--reference", type=Path, default=ROOT / ".private/reference")
    args = parser.parse_args()
    config = load_config(ROOT)
    for stage in [args.stage] if args.stage else CATALOG:
        verify(stage, config, args.reference)
