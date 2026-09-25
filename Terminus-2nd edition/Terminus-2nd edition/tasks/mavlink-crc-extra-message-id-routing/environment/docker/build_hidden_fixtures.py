"""Image-build helper: verifier streams at /opt/verifier-fixtures (not under /app)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

APP = Path("/app")
STREAMS = APP / "fixtures" / "streams"
OUT_ROOT = Path("/opt/verifier-fixtures/mavlink")
OUT_STREAMS = OUT_ROOT / "streams"


def build() -> None:
    OUT_STREAMS.mkdir(parents=True, exist_ok=True)
    hidden = [
        ("hidden-dedup-compid", "dedup-compid-trap.bin"),
        ("hidden-session-resume", "checkpoint-resume-session-trap.bin"),
    ]
    for name, src_name in hidden:
        shutil.copy2(STREAMS / src_name, OUT_STREAMS / f"{name}.bin")
    catalog = {
        "scenarios": [
            {"name": "hidden-dedup-compid", "stream": "streams/hidden-dedup-compid.bin"},
            {
                "name": "hidden-session-resume",
                "stream": "streams/hidden-session-resume.bin",
            },
        ]
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
