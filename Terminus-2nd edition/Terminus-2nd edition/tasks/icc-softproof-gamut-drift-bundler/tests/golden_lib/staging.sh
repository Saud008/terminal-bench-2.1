#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/parse_readings.sh"

write_staging_snapshot() {
  local readings_path="$1"
  local profile_path="$2"
  local paper_path="$3"
  local staging_path="$4"
  require_file "${readings_path}"
  require_file "${profile_path}"
  require_file "${paper_path}"
  local patches_json profile_id
  patches_json="$(parse_readings_json "${readings_path}")"
  profile_id="$(jq -r '.profile_id' "${profile_path}")"
  python3 - "${staging_path}" "${readings_path}" "${profile_path}" "${paper_path}" "${profile_id}" "${patches_json}" <<'PY'
import hashlib, json, sys
from pathlib import Path

staging_path = Path(sys.argv[1])
readings_path = Path(sys.argv[2])
profile_path = Path(sys.argv[3])
paper_path = Path(sys.argv[4])
profile_id = sys.argv[5]
patches = json.loads(sys.argv[6])

def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

doc = {
    "schema": "icc-softproof-stage/1",
    "readings_digest": digest_file(readings_path),
    "profile_digest": digest_file(profile_path),
    "paper_digest": digest_file(paper_path),
    "profile_id": profile_id,
    "patches": patches,
    "evaluation": None,
}
staging_path.parent.mkdir(parents=True, exist_ok=True)
staging_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

evaluate_staging_snapshot() {
  local staging_path="$1"
  local profile_path="$2"
  local paper_path="$3"
  local policy_path="$4"
  local tickets_path="$5"
  local as_of="$6"
  python3 - "${staging_path}" "${profile_path}" "${paper_path}" "${policy_path}" "${tickets_path}" "${as_of}" <<'PY'
import hashlib, json, math, sys
from pathlib import Path

staging_path = Path(sys.argv[1])
profile_path = Path(sys.argv[2])
paper_path = Path(sys.argv[3])
policy_path = Path(sys.argv[4])
tickets_path = Path(sys.argv[5])
as_of = int(sys.argv[6])

stage = json.loads(staging_path.read_text(encoding="utf-8"))
profile = json.loads(profile_path.read_text(encoding="utf-8"))
paper = json.loads(paper_path.read_text(encoding="utf-8"))
policy = json.loads(policy_path.read_text(encoding="utf-8"))
tickets_doc = json.loads(tickets_path.read_text(encoding="utf-8"))

def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def profile_checksum(doc):
    fields = doc.get("checksum_fields", [])
    subset = {k: doc[k] for k in fields if k in doc}
    payload = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def batch_index():
    return {b["id"]: b for b in paper.get("batches", [])}

def effective_gamma(batch_id):
    if not batch_id:
        return None
    idx = batch_index()
    current = batch_id
    visited = set()
    while current:
        if current in visited:
            return None
        visited.add(current)
        row = idx.get(current)
        if not row:
            return None
        anchor = row.get("gamma_anchor")
        if anchor is not None:
            return float(anchor)
        parent = row.get("parent")
        current = str(parent) if parent else ""
    return None

def pick_intent():
    supported = set(profile.get("rendering_intents", {}).keys())
    for intent in policy.get("intent_precedence", []):
        if intent in supported:
            return str(intent)
    return ""

def reference_lab(patch_id, intent):
    intent_map = profile.get("rendering_intents", {}).get(intent, {})
    if patch_id in intent_map:
        row = intent_map[patch_id]
    elif patch_id in profile.get("reference_patches", {}):
        row = profile["reference_patches"][patch_id]
    else:
        return None
    return float(row["L"]), float(row["a"]), float(row["b"])

def pick_ticket(profile_id, batch_id):
    hits = []
    for ticket in tickets_doc.get("tickets", []):
        if str(ticket.get("profile_id")) != profile_id:
            continue
        if str(ticket.get("paper_batch_id")) != batch_id:
            continue
        start = int(ticket.get("valid_from_epoch", 0))
        end = int(ticket.get("valid_until_epoch", 0))
        if as_of >= start and as_of <= end:
            hits.append(str(ticket.get("ticket_id", "")))
    return sorted(hits)[0] if hits else ""

intent = pick_intent()
checksum_ok = True
if policy.get("require_profile_checksum", False):
    checksum_ok = str(profile.get("checksum", "")) == profile_checksum(profile)
profile_id = str(profile.get("profile_id", ""))
per_patch = []
for patch in stage.get("patches", []):
    patch_id = str(patch["patch_id"])
    batch_id = str(patch.get("batch_id", ""))
    flags = []
    ref = reference_lab(patch_id, intent)
    delta_e = 0.0
    if ref is None:
        flags.append("MISSING_REFERENCE_PATCH")
    else:
        delta_e = math.sqrt(
            (float(patch["L"]) - ref[0]) ** 2
            + (float(patch["a"]) - ref[1]) ** 2
            + (float(patch["b"]) - ref[2]) ** 2
        )
        if delta_e > float(policy.get("delta_e_threshold", 2.0)):
            flags.append("DRIFT_DELTA_E")
    gamma = effective_gamma(batch_id)
    prof_gamma = float(profile.get("gamma_reference", 0.0))
    if gamma is not None and abs(gamma - prof_gamma) > float(policy.get("gamma_drift_threshold", 0.01)):
        flags.append("GAMMA_LINEAGE_DRIFT")
    ticket_id = pick_ticket(profile_id, batch_id) if batch_id else ""
    if batch_id and not ticket_id:
        flags.append("TICKET_EPOCH_INVALID")
    if not checksum_ok:
        flags.append("PROFILE_CHECKSUM_MISMATCH")
    per_patch.append(
        {
            "patch_id": patch_id,
            "delta_e": round(delta_e, 6),
            "active_intent": intent,
            "effective_gamma": gamma,
            "ticket_id": ticket_id,
            "drift_flags": sorted(flags),
        }
    )
per_patch.sort(key=lambda row: row["patch_id"])
stage["evaluation"] = {
    "policy_digest": digest_file(policy_path),
    "evaluated_as_of": as_of,
    "profile_checksum_ok": checksum_ok,
    "per_patch": per_patch,
}
staging_path.write_text(json.dumps(stage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

update_run_registry() {
  local readings_path="$1"
  local registry_path="${2:-/app/state/run-registry.json}"
  python3 - "${readings_path}" "${registry_path}" <<'PY'
import hashlib, json, sys
from pathlib import Path

readings_path = Path(sys.argv[1])
registry_path = Path(sys.argv[2])
digest = hashlib.sha256(readings_path.read_bytes()).hexdigest()
doc = {"runs": []}
if registry_path.is_file():
    doc = json.loads(registry_path.read_text(encoding="utf-8"))
runs = doc.setdefault("runs", [])
if not runs or runs[-1].get("readings_digest") != digest:
    runs.append({"readings_digest": digest, "count": 1})
else:
    runs[-1]["count"] = int(runs[-1].get("count", 0)) + 1
registry_path.parent.mkdir(parents=True, exist_ok=True)
registry_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
