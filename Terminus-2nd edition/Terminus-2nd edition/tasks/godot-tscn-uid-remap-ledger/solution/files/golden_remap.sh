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
suffix_mod = int(seeds_cfg.get("remap_suffix_mod", 5))
if slot:
    remap[slot] = f"{prefix}_{seed % suffix_mod}"
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
import json, os, re
content = os.environ["CONTENT"]
remap = json.loads(os.environ["REMAP_JSON"])
uid_re = re.compile(r'uid="(uid://[^"]+)"')
for old, new in sorted(remap.items(), key=lambda kv: -len(kv[0])):
    content = content.replace(f'uid="{old}"', f'uid="{new}"')
print(content, end="")
PY
}
