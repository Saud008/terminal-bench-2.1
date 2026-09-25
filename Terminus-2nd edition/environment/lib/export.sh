#!/usr/bin/env bash
# Scaffold: implement per /app/docs/export-schema.md

init_session_state() {
  printf '%s\n' '{"releases_attempted":0,"releases_succeeded":0,"releases_failed":0,"duplicate_skipped":0,"release_log":[]}' \
    > /app/work/session-state.json
}

append_session_json() {
  :
}

emit_export() {
  local scenario="$1"
  local seed="$2"
  local out="$3"
  python3 - "$scenario" "$seed" "$out" <<'PY'
import json, sys
scenario, seed, out = sys.argv[1:4]
doc = {
    "export_version": 1,
    "scenario": scenario,
    "seed": seed,
    "releases_attempted": 0,
    "releases_succeeded": 0,
    "releases_failed": 0,
    "duplicate_skipped": 0,
    "ledger_tail_sequence": 0,
    "release_epoch": 0,
    "policy_digest": "",
    "prepare_fingerprint": "",
    "custody_root": "",
    "pending_in_spool": {"spam": [], "virus": []},
    "release_log": [],
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}
