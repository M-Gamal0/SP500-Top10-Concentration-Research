"""Operational boundaries: portable paths, read-only source, rollback, lineage."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import duckdb
import pandas as pd

from sp500_top10.config import load_config
from sp500_top10.data.database import Repository
from sp500_top10.market_data.snapshot import load_snapshot
from sp500_top10.pipeline import validate_prerequisite
from sp500_top10.reporting.csv_export import publish_csvs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from create_synthetic import create

sys.path.insert(0, str(ROOT / "tools"))
from recover_csv_publication import recover


class OperationalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="sp500-test-")
        # Windows temporary paths may use an 8.3 alias; match load_config's canonical paths.
        cls.root = Path(cls.temporary.name).resolve()
        cls.source = create(cls.root, end="1999-03-31")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_portable_paths_do_not_follow_working_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_config(self.root)
        self.assertEqual(config.paths.source, self.source)
        self.assertEqual(config.paths.outputs, self.root / "outputs")

    def test_source_read_only_and_result_rollback(self):
        result = self.root / "rollback.duckdb"
        with Repository(self.source, result) as repository:
            with self.assertRaises(duckdb.InvalidInputException):
                repository.connection.execute("DELETE FROM private_source.main.stocks")
            repository.write({"target": pd.DataFrame({"x": [1]})}, "construction", "id", "run")
            with self.assertRaises(Exception):
                repository.write(
                    {"target": pd.DataFrame({"x": [2]}), "bad": pd.DataFrame()},
                    "construction",
                    "id",
                    "bad",
                )
            self.assertEqual(repository.query("SELECT x FROM target")["x"].tolist(), [1])

    def test_lineage_detects_manual_edits(self):
        with Repository(self.source, self.root / "lineage.duckdb") as repository:
            repository.write({"target": pd.DataFrame({"x": [1]})}, "construction", "id", "run")
            validate_prerequisite(repository, "construction", {"construction": "id"})
            repository.connection.execute("UPDATE target SET x=2")
            with self.assertRaisesRegex(ValueError, "changed outside"):
                validate_prerequisite(repository, "construction", {"construction": "id"})

    def test_csv_publication_rollback(self):
        output = self.root / "exports"
        publish_csvs({"a.csv": pd.DataFrame({"x": [1]})}, output, "first")
        original = (output / "a.csv").read_bytes()
        replace_file = Path.replace

        def fail_second(path, target):
            if path.name == "b.csv":
                raise OSError("simulated publication failure")
            return replace_file(path, target)

        with patch.object(Path, "replace", fail_second):
            with self.assertRaises(OSError):
                publish_csvs(
                    {"a.csv": pd.DataFrame({"x": [2]}), "b.csv": pd.DataFrame({"x": [3]})},
                    output,
                    "second",
                )
        self.assertEqual((output / "a.csv").read_bytes(), original)
        self.assertEqual(
            json.loads((output / ".publication.json").read_text())["status"], "complete"
        )

    def test_relocation_with_spaces_from_unrelated_directory(self):
        import shutil

        moved = self.root / "Moved Project With Spaces"
        moved.mkdir()
        shutil.copy2(ROOT / "run.py", moved / "run.py")
        shutil.copytree(ROOT / "src", moved / "src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(self.root / "data", moved / "data")
        env = {k: v for k, v in os.environ.items() if not k.startswith("SP500_")}
        run = subprocess.run(
            [sys.executable, str(moved / "run.py"), "--stage", "construction"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue((moved / "data/sp500_results.duckdb").exists())
        self.assertFalse((self.root / "data/sp500_results.duckdb").exists())

    def test_interrupted_publication_recovery(self):
        output = self.root / "interrupted"
        backup = output / ".publication/run/previous"
        backup.mkdir(parents=True)
        (backup / "a.csv").write_text("x\n1\n")
        (output / "a.csv").write_text("x\n2\n")
        (output / "b.csv").write_text("x\n3\n")
        (output / ".publication.json").write_text(
            json.dumps(
                {
                    "status": "publishing",
                    "backup": ".publication/run/previous",
                    "files": {"a.csv": {}, "b.csv": {}},
                }
            )
        )
        recover(output)
        self.assertEqual((output / "a.csv").read_text(), "x\n1\n")
        self.assertFalse((output / "b.csv").exists())
        self.assertEqual(
            json.loads((output / ".publication.json").read_text())["status"],
            "recovered_previous_set",
        )

    def test_corrupted_snapshot_rejected_before_calculation(self):
        import shutil

        directory = self.root / "corrupted_snapshot"
        shutil.copytree(self.root / "cache/market_data", directory)
        with (directory / "benchmark_daily.parquet").open("ab") as stream:
            stream.write(b"corruption")
        with self.assertRaisesRegex(ValueError, "checksum failed"):
            settings = replace(
                load_config(self.root).market_data, backtest_end_date=pd.Timestamp("1999-03-31")
            )
            load_snapshot(directory, settings, pd.DataFrame())


if __name__ == "__main__":
    unittest.main()
