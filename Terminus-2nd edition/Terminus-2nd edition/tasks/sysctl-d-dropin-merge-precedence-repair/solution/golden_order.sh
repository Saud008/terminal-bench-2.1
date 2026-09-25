#!/usr/bin/env bash

compute_drop_in_order() {
  local tree="$1"
  local seed="$2"
  python3 - "$tree" "$seed" <<'PY'
import hashlib, json, sys
from pathlib import Path

tree = Path(sys.argv[1])
seed = sys.argv[2]
manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
drop_ins = list(manifest.get("drop_ins", []))
drop_ins.sort(key=lambda rel: hashlib.sha256(f"{seed}:{rel}".encode()).hexdigest())
print("\n".join(drop_ins))
PY
}
