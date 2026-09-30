import json
import re
import sys
from pathlib import Path

SLUG = "gleaner-gitignore-match-repair"
CANON = f"/terminal-bench2.1/{SLUG}"
HOST = re.compile(r"(/home/saud|/mnt/c/|/Users/|/private/tmp/)")
root = Path(sys.argv[1])
apply = "--apply" in sys.argv


def fix(key, val, where):
    if not isinstance(val, str) or not HOST.search(val):
        return val
    new = f"file://{CANON}" if val.startswith("file://") else CANON
    print(f"{where}: {key}: {val!r} -> {new!r}")
    return new


def walk(obj, where):
    if isinstance(obj, dict):
        return {k: walk(v, where) if isinstance(v, (dict, list)) else fix(k, v, where) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v, where) if isinstance(v, (dict, list)) else fix("[]", v, where) for v in obj]
    return obj


for f in sorted(root.glob("run-*/*.json")):
    raw = f.read_text(encoding="utf-8")
    data = json.loads(raw)
    new = walk(data, str(f.relative_to(root)))
    if apply and new != data:
        f.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

