"""Portable run identities, input fingerprints, and durable local manifests."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path


def normalize(value):
    if is_dataclass(value):
        return normalize(asdict(value))
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, set):
        return sorted(normalize(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(normalize(value), sort_keys=True).encode()).hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(normalize(value), indent=2), encoding="utf-8")
    temporary.replace(path)


def artifact_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


class RunContext:
    def __init__(self, config, offline: bool):
        self.run_id = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        )
        self.path = config.paths.logs / (self.run_id + ".json")
        self.manifest = {
            "run_id": self.run_id,
            "status": "running",
            "offline": offline,
            "python": sys.version,
            "packages": {
                name: importlib.metadata.version(name)
                for name in ["duckdb", "numpy", "pandas", "statsmodels", "yfinance"]
            },
            "configuration": {
                name: normalize(getattr(config, name))
                for name in [
                    "construction",
                    "backtesting",
                    "market_data",
                    "analytics",
                    "factors",
                ]
            },
            "paths": {
                name: artifact_path(getattr(config.paths, name), config.paths.root)
                for name in ["source", "results", "outputs", "cache"]
            },
            "stages": {},
        }
        self.save()

    def save(self):
        save_json(self.path, self.manifest)
