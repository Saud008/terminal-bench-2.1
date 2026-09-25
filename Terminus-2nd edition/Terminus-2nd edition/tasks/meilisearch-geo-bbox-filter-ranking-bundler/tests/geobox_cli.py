from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def wipe_runtime() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def geobox(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full = os.environ.copy()
    if env:
        full.update(env)
    return subprocess.run(
        ["/app/bin/geoboxplay", *args],
        capture_output=True,
        text=True,
        env=full,
        check=False,
    )


def drive_score_round(
    level: str,
    run_id: str,
    *,
    output: str = "/app/output/geo-filter-playtest-atlas.json",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    full = os.environ.copy()
    if env:
        full.update(env)
    subprocess.run(
        ["/app/bin/geoboxplay", "load-level", "--level", level, "--run-id", run_id],
        capture_output=True,
        text=True,
        env=full,
        check=True,
    )
    subprocess.run(
        ["/app/bin/geoboxplay", "score-round", "--run-id", run_id],
        capture_output=True,
        text=True,
        env=full,
        check=True,
    )
    subprocess.run(
        ["/app/bin/geoboxplay", "seal-atlas", "--run-id", run_id, "--output", output],
        capture_output=True,
        text=True,
        env=full,
        check=True,
    )
    return json.loads(Path(output).read_text(encoding="utf-8"))
