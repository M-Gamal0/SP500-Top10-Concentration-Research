"""Restore the previous CSV set after an interrupted publication."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def recover(directory: Path) -> None:
    directory = directory.resolve(strict=True)
    marker = directory / ".publication.json"
    state = json.loads(marker.read_text(encoding="utf-8"))
    if state.get("status") != "publishing":
        raise ValueError("No interrupted publication is recorded.")
    backup = (directory / state["backup"]).resolve(strict=True)
    if not backup.is_relative_to(directory / ".publication"):
        raise ValueError("Backup path is outside the publication directory.")
    for name in state["files"]:
        if Path(name).name != name or not name.endswith(".csv"):
            raise ValueError("Invalid filename in publication record.")
    for name in state["files"]:
        previous = backup / name
        target = directory / name
        if previous.exists():
            shutil.copy2(previous, target)
        else:
            target.unlink(missing_ok=True)
    state["status"] = "recovered_previous_set"
    temporary = marker.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary.replace(marker)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    recover(args.directory)
    print("Previous CSV set restored. Rerun the affected stage to publish new results.")
