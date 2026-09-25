"""Offline yard fixture lint."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path("/app/fixtures/scenarios")
    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "scenario_id" in data
        assert data["procedure"]
    print("yard lint ok", len(list(root.glob("*.json"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
