#!/usr/bin/env bash

build_snapshot() {
  local tree="$1"
  local seed="$2"
  local snap="$3"
  python3 - "$tree" "$seed" "$snap" <<'PY'
import json, subprocess, sys
from pathlib import Path

tree, seed, snap = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))

def run_bash(fn, *args):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    if fn == "parse":
        cmd = [
            "bash",
            "-c",
            'source /app/lib/common.sh; source /app/lib/parse.sh; parse_fragment "$1"',
            "bash",
            *args,
        ]
    elif fn == "order":
        cmd = [
            "bash",
            "-c",
            'source /app/lib/common.sh; source /app/lib/order.sh; compute_drop_in_order "$1" "$2"',
            "bash",
            *args,
        ]
    elif fn == "layers":
        cmd = [
            "bash",
            "-c",
            'source /app/lib/common.sh; source /app/lib/layers.sh; merge_fragment_into_state "$1" "$2" "$3"',
            "bash",
            *args,
        ]
    else:
        raise ValueError(fn)
    return subprocess.check_output(cmd, env=env, text=True).strip()

files = []
main = manifest.get("main")
if main:
    files.append(main)
order_raw = run_bash("order", str(tree), seed)
files.extend([ln for ln in order_raw.splitlines() if ln.strip()])

effective = {}
sources = {}
for rel in files:
    parsed = json.loads(run_bash("parse", str(tree / rel)))
    if parsed["errors"]:
        sys.exit(3)
    state_json = json.dumps({"effective": effective, "sources": sources})
    updated = json.loads(run_bash("layers", str(tree / rel), rel, state_json))
    effective = updated["effective"]
    sources = updated["sources"]

doc = {
    "snapshot_version": 1,
    "tree_path": str(tree),
    "tree": tree.name,
    "seed": seed,
    "processing_order": files,
    "effective": effective,
    "sources": sources,
    "stats": {"keys": len(effective), "files_processed": len(files)},
}
snap.parent.mkdir(parents=True, exist_ok=True)
snap.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
  local rc=$?
  if [[ "$rc" -ne 0 ]]; then
    return "$rc"
  fi
  write_merge_staging "$snap"
  append_replay_record "$snap"
}
