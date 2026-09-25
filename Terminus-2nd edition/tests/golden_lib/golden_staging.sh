#!/usr/bin/env bash

write_release_staging() {
  compute_policy_digest
  local digest="${POLICY_DIGEST:-}"
  python3 - "$digest" <<'PY'
import json, sys
from pathlib import Path

digest = sys.argv[1]
manifest_path = Path("/app/state/spool-manifest.json")
manifest = {"messages": []}
if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

epoch = 0
epoch_path = Path("/app/state/release-epoch.json")
if epoch_path.is_file():
    try:
        epoch = int(json.loads(epoch_path.read_text(encoding="utf-8")).get("epoch", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        epoch = 0

pending = {"spam": [], "virus": []}
index = {}
for row in manifest.get("messages", []):
    qid = row["quarantine_id"]
    sub = row.get("spool_subdir", row.get("stored_class", "spam"))
    stored = row.get("stored_class", sub)
    index[qid] = {"stored_class": stored, "spool_subdir": sub}
    eml = Path(f"/app/work/spool/{sub}/msg.{qid}.eml")
    if eml.is_file() and qid not in pending[stored]:
        pending[stored].append(qid)

for cls in pending:
    pending[cls] = sorted(pending[cls])

doc = {
    "staging_written": False,
    "release_epoch": epoch,
    "policy_digest": digest,
    "pending_in_spool": pending,
    "index": index,
}
Path("/app/state/release-staging.json").write_text(
    json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY
}
