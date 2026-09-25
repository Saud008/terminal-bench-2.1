#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_load_remap_table() {
  local tree="$1" seed="$2"
  python3 - "${tree}" "${seed}" <<'PY'
import json, sys
from pathlib import Path

tree = Path(sys.argv[1])
seed = int(sys.argv[2])
seeds_cfg = json.loads((tree.parent.parent / "seeds.json").read_text(encoding="utf-8"))
remap = json.loads((tree / "remap.json").read_text(encoding="utf-8"))
slot = seeds_cfg.get("remap_slot")
prefix = seeds_cfg.get("remap_prefix", "uid://player_new")
if slot:
    remap[slot] = f"{prefix}_{seed % 5}"
print(json.dumps(remap))
PY
}

tscn_apply_remap_to_text() {
  local content="$1" remap_json="$2"
  if [[ -z "${content}" && -n "${TSCN_CONTENT:-}" ]]; then
    content="${TSCN_CONTENT}"
  fi
  if [[ -z "${remap_json}" && -n "${TSCN_REMAP_JSON:-}" ]]; then
    remap_json="${TSCN_REMAP_JSON}"
  fi
  CONTENT="${content}" REMAP_JSON="${remap_json}" python3 <<'PY'
import json, os
content = os.environ["CONTENT"]
remap = json.loads(os.environ["REMAP_JSON"])
for old, new in remap.items():
    old_path = old.replace("uid://", "")
    new_path = new.replace("uid://", "")
    content = content.replace(f"res://{old_path}.tscn", f"res://{new_path}.tscn")
    content = content.replace(f"res://{old_path}.gd", f"res://{new_path}.gd")
print(content, end="")
PY
}
