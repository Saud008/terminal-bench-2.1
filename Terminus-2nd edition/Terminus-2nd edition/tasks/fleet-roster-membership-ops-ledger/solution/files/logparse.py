from __future__ import annotations

import json
from pathlib import Path


def read_cluster_logs(scenario_dir: str | Path) -> list[dict]:
    rows: list[dict] = []
    root = Path(scenario_dir)
    for path in sorted(root.glob("*.qlog")):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    rows.sort(key=lambda r: (r["term"], r["index"]))
    return rows
