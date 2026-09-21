"""Stage complete CSV sets before replacement; retain recoverable backups."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from ..run_context import digest_file, save_json


def publish_csvs(frames: dict[str, pd.DataFrame], output: Path, run_id: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    staging = output / ".publication" / run_id
    backups = staging / "previous"
    staging.mkdir(parents=True, exist_ok=False)
    backups.mkdir()
    marker = output / ".publication.json"
    if (
        marker.exists()
        and json.loads(marker.read_text(encoding="utf-8")).get("status") == "publishing"
    ):
        raise RuntimeError(
            f"Interrupted CSV publication at {output}; restore backups before publishing."
        )
    prepared = {}
    for name, frame in frames.items():
        if Path(name).name != name or not name.endswith(".csv"):
            raise ValueError(f"Invalid CSV filename: {name}")
        path = staging / name
        frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d", na_rep="")
        actual = pd.read_csv(path, keep_default_na=False)
        if list(actual.columns) != list(frame.columns) or len(actual) != len(frame):
            raise ValueError(f"{name}: CSV structural verification failed.")
        # Verify the serialized cell values, including strings that look like NA.
        from io import StringIO

        expected = pd.read_csv(
            StringIO(frame.to_csv(index=False, date_format="%Y-%m-%d", na_rep="")),
            keep_default_na=False,
        )
        pd.testing.assert_frame_equal(actual, expected, check_exact=True)
        prepared[name] = {"rows": len(frame), "sha256": digest_file(path)}
        if (output / name).exists():
            shutil.copy2(output / name, backups / name)
    old_marker = marker.read_bytes() if marker.exists() else None
    save_json(
        marker,
        {
            "status": "publishing",
            "run_id": run_id,
            "files": prepared,
            "backup": str(backups.relative_to(output)),
        },
    )
    replaced = []
    try:
        for name in frames:
            (staging / name).replace(output / name)
            replaced.append(name)
        save_json(marker, {"status": "complete", "run_id": run_id, "files": prepared})
    except BaseException:
        for name in reversed(replaced):
            previous = backups / name
            if previous.exists():
                previous.replace(output / name)
            else:
                (output / name).unlink(missing_ok=True)
        if old_marker is None:
            save_json(marker, {"status": "failed", "run_id": run_id})
        else:
            marker.write_bytes(old_marker)
        raise
