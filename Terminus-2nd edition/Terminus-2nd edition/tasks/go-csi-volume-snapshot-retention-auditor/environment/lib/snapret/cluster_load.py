from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cluster(scenario: str, fixture_root: str = "/app/fixtures") -> dict[str, Any]:
    if not fixture_root:
        fixture_root = "/app/fixtures"
    cluster_path = Path(fixture_root) / "clusters" / scenario / "cluster.json"
    return json.loads(cluster_path.read_text(encoding="utf-8"))
