#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent / "scenarios"
assert root.is_dir(), "missing scenarios"
paths = sorted(root.glob("*.json"))
print("auction fixtures ok", len(paths))
for path in paths:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    payload = json.loads(raw.read_text(encoding="utf-8"))
    assert payload.get("scenario_id"), f"missing scenario_id in {path.name}"
    print(path.name, digest)
