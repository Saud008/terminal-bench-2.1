#!/usr/bin/env bash

init_session_state() {
  python3 - <<'PY'
import json
doc = {
    "releases_attempted": 0,
    "releases_succeeded": 0,
    "releases_failed": 0,
    "duplicate_skipped": 0,
    "release_log": [],
}
with open("/app/work/session-state.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

append_session_json() {
  python3 - "$1" <<'PY'
import json, os, sys
patch = json.loads(sys.argv[1])
path = "/app/work/session-state.json"
cur = {}
if os.path.isfile(path):
    cur = json.load(open(path, encoding="utf-8"))
for k, v in patch.items():
    if k == "release_log" and isinstance(v, list):
        cur.setdefault("release_log", []).extend(v)
    elif k in ("releases_attempted", "releases_succeeded", "releases_failed", "duplicate_skipped"):
        cur[k] = int(cur.get(k, 0)) + int(v)
    else:
        cur[k] = v
with open(path, "w", encoding="utf-8") as fh:
    json.dump(cur, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

emit_export() {
  local scenario="$1"
  local seed="$2"
  local out="$3"
  compute_custody_root
  python3 - "$scenario" "$seed" "$out" "${CUSTODY_ROOT:-}" "${SEAL_PATH}" <<'PY'
import json, os, sys
from pathlib import Path
scenario, seed, out, custody_root, seal_path = sys.argv[1:6]
state_path = "/app/work/session-state.json"
ledger_path = "/app/work/ledger.json"
staging_path = "/app/state/release-staging.json"
epoch_path = "/app/state/release-epoch.json"
state = {}
if os.path.isfile(state_path):
    state = json.load(open(state_path, encoding="utf-8"))
ledger = {"entries": []}
if os.path.isfile(ledger_path):
    ledger = json.load(open(ledger_path, encoding="utf-8"))
released_ids = {
    e["quarantine_id"]
    for e in ledger.get("entries", [])
    if e.get("status") == "released"
}
pending = {"spam": [], "virus": []}
staging_epoch = 0
policy_digest = ""
if os.path.isfile(staging_path):
    staging = json.load(open(staging_path, encoding="utf-8"))
    staging_epoch = int(staging.get("release_epoch", 0) or 0)
    policy_digest = staging.get("policy_digest", "") or ""
    base = staging.get("pending_in_spool", {})
    for cls in ("spam", "virus"):
        pending[cls] = sorted(q for q in base.get(cls, []) if q not in released_ids)
else:
    for cls, sub in (("spam", "spam"), ("virus", "virus")):
        root = Path(f"/app/work/spool/{sub}")
        if not root.is_dir():
            continue
        for eml in sorted(root.glob("msg.*.eml")):
            qid = eml.name.removeprefix("msg.").removesuffix(".eml")
            if qid not in released_ids:
                pending[cls].append(qid)
file_epoch = 0
if os.path.isfile(epoch_path):
    try:
        file_epoch = int(json.load(open(epoch_path, encoding="utf-8")).get("epoch", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        file_epoch = 0
# Export must publish staging epoch and it must match the persisted epoch file.
release_epoch = staging_epoch if staging_epoch == file_epoch else 0
tail = 0
for e in ledger.get("entries", []):
    if e.get("status") == "released" and "sequence" in e:
        tail = max(tail, int(e["sequence"]))
prepare_fingerprint = ""
if os.path.isfile(seal_path):
    try:
        seal = json.load(open(seal_path, encoding="utf-8"))
        prepare_fingerprint = seal.get("prepare_fingerprint", "") or ""
    except (json.JSONDecodeError, TypeError, ValueError):
        prepare_fingerprint = ""
doc = {
    "export_version": 1,
    "scenario": scenario,
    "seed": seed,
    "releases_attempted": state.get("releases_attempted", 0),
    "releases_succeeded": state.get("releases_succeeded", 0),
    "releases_failed": state.get("releases_failed", 0),
    "duplicate_skipped": state.get("duplicate_skipped", 0),
    "ledger_tail_sequence": tail,
    "release_epoch": release_epoch,
    "policy_digest": policy_digest,
    "prepare_fingerprint": prepare_fingerprint,
    "custody_root": custody_root,
    "pending_in_spool": pending,
    "release_log": state.get("release_log", []),
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}
