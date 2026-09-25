#!/usr/bin/env bash

s2_emit_audit_manifest() {
  local staging="$1"
  local hooks_json="$2"
  local out="$3"
  python3 - "$staging" "$hooks_json" "$out" <<'PY'
import json
import sys

staging = json.load(open(sys.argv[1], encoding="utf-8"))
hooks_doc = json.load(open(sys.argv[2], encoding="utf-8"))
snap = json.load(open(staging["snapshot_path"], encoding="utf-8"))
hook_results = hooks_doc.get("hooks", [])
hooks_ok = all(h.get("exit", 1) == 0 for h in hook_results)
ok = bool(staging.get("hooks_ok")) and hooks_ok
doc = {
    "pipeline_version": 1,
    "seed": staging["seed"],
    "rootfs": staging["rootfs"],
    "mount_steps": snap.get("mount_steps", []),
    "hooks": hook_results,
    "resolv_target": staging.get("resolv_target", ""),
    "sources_digest": staging.get("sources_digest", ""),
    "ok": ok,
}
with open(sys.argv[3], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
