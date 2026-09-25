import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent / "cycles"
paths = sorted(root.glob("*.json"))
print("subled fixtures ok", len(paths))
for path in paths:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("scenario_id"), path.name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    print(path.name, digest)
