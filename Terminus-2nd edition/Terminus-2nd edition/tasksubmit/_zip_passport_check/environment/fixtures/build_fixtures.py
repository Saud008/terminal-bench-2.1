import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent / "scenarios"
assert root.is_dir(), "missing scenarios"
paths = sorted(root.glob("*.json"))
print("pvw fixtures ok", len(paths))
assert len(paths) >= 8, "need at least 8 bundled scenarios"
for path in paths:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    payload = json.loads(raw.decode("utf-8"))
    assert payload.get("scenario_id"), f"missing scenario_id in {path.name}"
    assert payload.get("reference_date"), f"missing reference_date in {path.name}"
    print(path.name, digest)
