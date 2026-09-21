"""Bounded provider I/O and local provenance for newly retrieved payloads."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..run_context import save_json


def retry(operation, attempts=3):
    for attempt in range(attempts):
        try:
            return operation()
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except (URLError, OSError, TimeoutError):
            if attempt == attempts - 1:
                raise
        time.sleep(min(2**attempt, 4))


def retrieve(url: str, raw_dir: Path | None = None) -> bytes:
    def request():
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
            return response.read()

    payload = retry(request)
    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(url.encode()).hexdigest()
        (raw_dir / (name + ".payload")).write_bytes(payload)
        save_json(
            raw_dir / (name + ".json"),
            {
                "url": url,
                "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": hashlib.sha256(payload).hexdigest(),
            },
        )
    return payload
