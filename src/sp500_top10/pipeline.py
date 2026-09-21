"""Deterministic stage orchestration, compatibility lineage, and durable status."""

from __future__ import annotations

import importlib
import json
import logging
import time
from dataclasses import asdict
from pathlib import Path

from .data.database import Repository
from .market_data.snapshot import load_snapshot, save_snapshot
from .reporting.catalog import CATALOG
from .reporting.csv_export import publish_csvs
from .run_context import RunContext, digest_file, fingerprint

STAGES = {
    "construction": ("construction", []),
    "backtesting": ("backtesting", ["construction"]),
    "market-data": ("market_data", ["backtesting"]),
    "analytics": ("analytics", ["construction", "backtesting", "market-data"]),
    "factor-attribution": ("factors", ["backtesting", "market-data"]),
}


def validate_prerequisite(repository, stage, stage_ids, visited=None):
    """Reject stale, incomplete, or externally modified upstream outputs."""
    visited = visited if visited is not None else {}
    if stage in visited:
        return visited[stage]
    record = repository.stage_record(stage)
    if record is None or record[0] != stage_ids[stage] or record[2] != 2:
        raise ValueError(f"Prerequisite {stage} is missing or stale; rerun it first.")
    payload = json.loads(record[1])
    if not payload.get("complete"):
        raise ValueError(f"Prerequisite {stage} did not complete publication.")
    for dependency in STAGES[stage][1]:
        current = validate_prerequisite(repository, dependency, stage_ids, visited)
        if payload["dependencies"].get(dependency) != current:
            raise ValueError(f"Prerequisite {stage} was built from outdated {dependency} outputs.")
    for table, identity in payload["tables"].items():
        if fingerprint(repository.table_identity(table)) != fingerprint(identity):
            raise ValueError(f"Prerequisite table {table} changed outside its recorded run.")
    signature = fingerprint(payload)
    visited[stage] = signature
    return signature


def execute(config, selected: str | None = None, offline: bool = False):
    logger = logging.getLogger(__name__)
    context = RunContext(config, offline)
    try:
        source_id = digest_file(config.paths.source)
        code_root = Path(__file__).parent
        code_id = fingerprint(
            {
                p.relative_to(code_root).as_posix(): digest_file(p)
                for p in sorted(code_root.rglob("*"))
                if p.suffix in {".py", ".sql"}
            }
        )
        # Source contents and effective settings define identity, not checkout paths.
        stage_ids = {}
        for name, (area, dependencies) in STAGES.items():
            stage_ids[name] = fingerprint(
                {
                    "source": source_id,
                    "code": code_id,
                    "settings": asdict(getattr(config, area)),
                    "dependencies": {dep: stage_ids[dep] for dep in dependencies},
                }
            )
        context.manifest.update(source_sha256=source_id, code_sha256=code_id)
        context.save()
        with Repository(config.paths.source, config.paths.results) as repository:
            for name, (area, dependencies) in STAGES.items():
                if selected and selected != name:
                    continue
                checked = {}
                dependency_signatures = {
                    dependency: validate_prerequisite(repository, dependency, stage_ids, checked)
                    for dependency in dependencies
                }
                logger.info("Starting %s", name)
                started = time.monotonic()
                context.manifest["stages"][name] = {"status": "running"}
                context.save()
                settings = getattr(config, area)
                if name == "market-data" and offline:
                    calendar = repository.query(
                        "SELECT DISTINCT date FROM backtest_daily_index ORDER BY date"
                    )
                    result = load_snapshot(config.paths.cache / "market_data", settings, calendar)
                elif name == "market-data":
                    result = importlib.import_module(".market_data.stage", __package__).run(
                        repository, settings, raw_dir=config.paths.cache / "raw" / context.run_id
                    )
                else:
                    result = importlib.import_module(f".{area}.stage", __package__).run(
                        repository, settings
                    )
                if set(result.tables) != set(CATALOG[name]["tables"]) or set(result.csvs) != set(
                    CATALOG[name]["csvs"]
                ):
                    raise ValueError(
                        f"{name}: output registry differs from the compatibility contract."
                    )
                repository.write(
                    result.tables,
                    name,
                    stage_ids[name],
                    context.run_id,
                    dependency_signatures,
                    complete=False,
                )
                if name == "market-data" and not offline:
                    save_snapshot(
                        result.tables,
                        config.paths.cache / "market_data",
                        settings,
                        "online provider refresh; normalized outputs",
                    )
                if result.csvs:
                    group = "factor_attribution" if name == "factor-attribution" else "analytics"
                    publish_csvs(result.csvs, config.paths.outputs / group, context.run_id)
                repository.mark_complete(name)
                counts = {table: len(frame) for table, frame in result.tables.items()}
                coverage = {}
                for table, frame in result.tables.items():
                    for column in [
                        "date",
                        "Date",
                        "month_end",
                        "selection_date",
                        "window_end",
                        "observation_date",
                    ]:
                        if column in frame and not frame.empty:
                            coverage[table] = {
                                "column": column,
                                "first": str(frame[column].min()),
                                "last": str(frame[column].max()),
                            }
                            break
                context.manifest["stages"][name] = {
                    "status": "complete",
                    "seconds": round(time.monotonic() - started, 3),
                    "rows": counts,
                    "coverage": coverage,
                    "csv_count": len(result.csvs),
                    "fingerprint": stage_ids[name],
                }
                context.save()
                logger.info(
                    "Saved %s: %d tables, %d CSVs (%.1fs)",
                    name,
                    len(result.tables),
                    len(result.csvs),
                    time.monotonic() - started,
                )
        if digest_file(config.paths.source) != source_id:
            raise RuntimeError(
                "Source database changed during the run; results require verification."
            )
        context.manifest["status"] = "complete"
        context.save()
        return context
    except BaseException as error:
        context.manifest["status"] = "failed"
        context.manifest["error"] = f"{type(error).__name__}: {error}"
        context.save()
        raise
