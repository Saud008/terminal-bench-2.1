#!/usr/bin/env bash

s2_run_stage2_hooks() {
  local rootfs="$1"
  local out_json="$2"
  if [[ "${S2_COMMITTED:-0}" != "1" ]]; then
    python3 - "$out_json" <<'PY'
import json
import sys

doc = {"hooks": [{"name": "__blocked__", "exit": 1}]}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
    return 0
  fi
  export STAGE2_ROOT="${rootfs}/tree"
  python3 - "$rootfs" "$out_json" <<'PY'
import json
import os
import subprocess
import sys

rootfs, out_path = sys.argv[1:3]
hook_dir = os.path.join(rootfs, "hooks", "stage2.d")
results = []
if os.path.isdir(hook_dir):
    for name in sorted(os.listdir(hook_dir)):
        if not name.endswith(".sh"):
            continue
        path = os.path.join(hook_dir, name)
        proc = subprocess.run(
            ["bash", path],
            env={**os.environ, "STAGE2_ROOT": os.path.join(rootfs, "tree")},
        )
        results.append({"name": name, "exit": proc.returncode})
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({"hooks": results}, fh, indent=2)
    fh.write("\n")
PY
}
