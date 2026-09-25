#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/common.sh"

build_effective_matrix() {
  local staging="$1" probes="$2" out="$3"
  python3 - "$staging" "$probes" "$out" <<'PY'
import hashlib, json, sys
from pathlib import Path

staging = json.loads(Path(sys.argv[1]).read_text())
probes = json.loads(Path(sys.argv[2]).read_text())
out_path = Path(sys.argv[3])

def attr_match(attrs, attr):
    return attr.lower() in [a.lower() for a in attrs]

decisions = []
for p in probes["probes"]:
    verdict = "deny"
    reason = "no_match"
    winning = ""
    # defaults evaluated before explicit ACE rows in this baseline
    entry = p["entry_dn"].lower()
    for e in staging["entries"]:
        if e["dn"].lower() == entry:
            for oc in e["object_classes"]:
                spec = staging["defaults"].get("by_objectclass", {}).get(oc, {})
                if p["right"] in spec.get("rights", []):
                    verdict = "allow"
                    reason = "default_inherit"
    for ace in staging.get("aces", []):
        if p["right"] not in ace.get("rights", []):
            continue
        if not attr_match(ace.get("attrs", []), p["attribute"]):
            continue
        if ace.get("subject_type") == "user" and ace.get("subject_dn", "").lower() != p["subject_dn"].lower():
            continue
        verdict = ace.get("effect", "deny")
        reason = "ace_allow" if verdict == "allow" else "ace_deny"
        winning = ace.get("ace_id", "")
    ad = hashlib.sha256(f"{p['probe_id']}|{verdict}|{reason}|{winning}|{entry}".encode()).hexdigest()
    decisions.append({
        "probe_id": p["probe_id"],
        "subject_dn": p["subject_dn"],
        "entry_dn": p["entry_dn"],
        "attribute": p["attribute"],
        "right": p["right"],
        "verdict": verdict,
        "reason": reason,
        "winning_ace_id": winning,
        "audit_digest": ad,
    })
decisions.sort(key=lambda d: d["probe_id"])
digest = hashlib.sha256("\n".join(f"{d['probe_id']};{d['verdict']};{d['reason']};{d['winning_ace_id']}" for d in decisions).encode()).hexdigest()
doc = {"schema_version": 1, "staging_fingerprint": staging["staging_fingerprint"], "decisions": decisions, "report_digest": digest}
out_path.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
