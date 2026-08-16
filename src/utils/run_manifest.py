"""Run manifests.

Every script that touches data writes one JSON manifest next to its output: the
parameters it ran with, how many rows went in and out, how long it took, and the git
commit it ran from. The data funnel table in the report is assembled from these files,
so a number in the report can always be traced back to one run.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src import config


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=config.ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


@dataclass
class RunManifest:
    """Collects run metadata, then writes it as JSON.

    Usage:
        with RunManifest("crawl_chotot", params={"district": "Tân Bình"}) as m:
            m.count("requests", 214)
            m.count("listings_written", 5_180)
    """

    step: str
    params: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    git_sha: str = ""
    python: str = ""
    status: str = "running"

    _t0: float = field(default=0.0, repr=False)

    def __enter__(self) -> "RunManifest":
        self._t0 = time.time()
        self.started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.git_sha = _git_sha()
        self.python = f"{platform.python_version()} ({sys.platform})"
        return self

    def count(self, key: str, value: int) -> None:
        self.counts[key] = value

    def note(self, message: str) -> None:
        self.notes.append(message)

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.duration_seconds = round(time.time() - self._t0, 2)
        self.finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.status = "failed" if exc_type else "ok"
        if exc_type:
            self.note(f"{exc_type.__name__}: {exc}")
        self.write()
        return False  # never swallow the exception

    def path(self) -> Path:
        stamp = self.started_at.replace(":", "").replace("-", "")
        target = config.DATA / "_manifests"
        target.mkdir(parents=True, exist_ok=True)
        return target / f"{stamp}_{self.step}.json"

    def write(self) -> Path:
        payload = {k: v for k, v in asdict(self).items() if not k.startswith("_")}
        out = self.path()
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
