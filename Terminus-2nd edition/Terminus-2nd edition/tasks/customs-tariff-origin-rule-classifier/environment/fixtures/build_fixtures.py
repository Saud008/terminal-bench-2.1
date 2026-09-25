#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent / "manifests"
assert root.is_dir(), "missing manifests"
paths = sorted(root.glob("*.json"))
print("customs manifests ok", len(paths))
for path in paths:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("scenario_id"), f"missing scenario_id in {path.name}"
    assert payload.get("importer_id"), f"missing importer_id in {path.name}"
    print(path.name, digest)
