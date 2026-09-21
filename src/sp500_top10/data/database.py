"""DuckDB repository with read-only source attachment and transactional results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

SOURCE_COLUMNS = {
    "quarterly_company_universe": (
        "selection_date",
        "ticker",
        "name",
        "resolved_marketcap",
        "marketcap_source",
        "multi_class_company",
    ),
    "stocks": ("date", "ticker", "close", "closeadj"),
    "sp500": ("date", "action", "ticker", "name"),
    "daily": ("date", "ticker", "marketcap"),
    "tickers": ("ticker", "sector", "lastupdated"),
}


def identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class Repository:
    """One result writer; all source access is explicitly read-only."""

    def __init__(self, source: Path, results: Path):
        if not source.is_file():
            raise FileNotFoundError(
                f"Source database does not exist: {source}. Set SP500_SOURCE_DB."
            )
        if source.resolve() == results.resolve() or (results.exists() and source.samefile(results)):
            raise ValueError("Source and results must be different files.")
        results.parent.mkdir(parents=True, exist_ok=True)
        self.connection = duckdb.connect(str(results))
        try:
            escaped = str(source).replace("'", "''")
            self.connection.execute(f"ATTACH '{escaped}' AS private_source (READ_ONLY)")
            available = self.connection.execute(
                "SELECT table_name, column_name FROM information_schema.columns WHERE table_catalog='private_source'"
            ).fetchall()
            columns: dict[str, set[str]] = {}
            for table, column in available:
                columns.setdefault(table, set()).add(column)
            for table, required in SOURCE_COLUMNS.items():
                missing = set(required) - columns.get(table, set())
                if missing:
                    raise ValueError(f"Source table {table} missing columns: {sorted(missing)}")
                self.connection.execute(
                    f"CREATE TEMP VIEW {identifier(table)} AS SELECT * FROM private_source.main.{identifier(table)}"
                )
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS _pipeline_stages (stage VARCHAR PRIMARY KEY, fingerprint VARCHAR, run_id VARCHAR, outputs VARCHAR, schema_version INTEGER)"
            )
        except BaseException:
            self.connection.close()
            raise

    def query(self, sql: str, parameters=None) -> pd.DataFrame:
        return self.connection.execute(sql, parameters or []).df()

    def stage_record(self, stage: str):
        return self.connection.execute(
            "SELECT fingerprint, outputs, schema_version FROM _pipeline_stages WHERE stage=?",
            [stage],
        ).fetchone()

    def table_identity(self, table: str) -> dict:
        frame = self.query(f"SELECT * FROM {identifier(table)} ORDER BY ALL")
        schema = self.connection.execute(f"DESCRIBE {identifier(table)}").fetchall()
        digest = hashlib.sha256(
            pd.util.hash_pandas_object(frame, index=False).values.tobytes()
        ).hexdigest()
        return {"rows": len(frame), "schema": schema, "values_sha256": digest}

    def mark_complete(self, stage: str):
        record = self.stage_record(stage)
        payload = json.loads(record[1])
        payload["complete"] = True
        self.connection.execute(
            "UPDATE _pipeline_stages SET outputs=? WHERE stage=?", [json.dumps(payload), stage]
        )

    def write(
        self,
        tables: dict[str, pd.DataFrame],
        stage: str,
        fingerprint: str,
        run_id: str,
        dependency_signatures=None,
        complete=True,
    ):
        self.connection.execute("BEGIN TRANSACTION")
        try:
            for table, frame in tables.items():
                working = frame.copy()
                for column in working:
                    if isinstance(working[column].dtype, pd.PeriodDtype):
                        working[column] = working[column].dt.to_timestamp(how="end").dt.normalize()
                    if working.empty and working[column].dtype == object:
                        working[column] = working[column].astype("string")
                self.connection.register("_stage_frame", working)
                try:
                    self.connection.execute(
                        f"CREATE OR REPLACE TABLE {identifier(table)} AS SELECT * FROM _stage_frame"
                    )
                finally:
                    self.connection.unregister("_stage_frame")
                count = self.connection.execute(
                    f"SELECT count(*) FROM {identifier(table)}"
                ).fetchone()[0]
                if count != len(frame):
                    raise RuntimeError(f"{table}: stored row count differs.")
            payload = {
                "complete": complete,
                "dependencies": dependency_signatures or {},
                "tables": {table: self.table_identity(table) for table in tables},
            }
            self.connection.execute(
                "INSERT OR REPLACE INTO _pipeline_stages VALUES (?, ?, ?, ?, 2)",
                [stage, fingerprint, run_id, json.dumps(payload)],
            )
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.connection.close()
