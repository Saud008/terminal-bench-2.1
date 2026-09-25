#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../control/stack_walker.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../policy/group_gate.sh"

run_id=""
service=""
subject=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --service) service="$2"; shift 2 ;;
    --subject) subject="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$service" && -n "$subject" && -n "$output" ]] || { echo "missing flags" >&2; exit 2; }
[[ -f "$LEDGER" ]] || { echo "missing ledger" >&2; exit 2; }

svc_json="$(jq -c --arg s "$service" '.services[$s]' "$LEDGER")"
[[ "$svc_json" != "null" ]] || { echo "unknown service" >&2; exit 2; }

modules_json="$(echo "$svc_json" | jq -c '.modules')"
outcomes_json="$(jq -c '.outcomes' "$LEDGER")"
subjects_json="$(jq -c '.subjects' "$LEDGER")"

walk_json="$(walk_auth_stack "$modules_json" "$outcomes_json" "$subject")"

python3 - "$run_id" "$service" "$subject" "$walk_json" "$subjects_json" "$output" <<'PY'
import json, sys, hashlib
from pathlib import Path

run_id, service, subject = sys.argv[1:4]
walk = json.loads(sys.argv[4])
subjects = json.loads(sys.argv[5])
output = Path(sys.argv[6])

def subject_groups(doc, subject):
    users = doc.get("users", {})
    groups = doc.get("groups", {})
    direct = set(users.get(subject, {}).get("groups", []))
    return sorted(direct)

groups = subject_groups(subjects, subject)
steps = walk["steps"]
# trace sequence uses module lexicographic key
steps = sorted(steps, key=lambda s: s["module"])

report = {
    "run_id": run_id,
    "service": service,
    "subject": subject,
    "subject_groups": groups,
    "steps": steps,
    "verdict_code": walk["verdict_code"],
    "verdict": walk["verdict"],
    "reason": walk["reason"],
}
digest_src = json.dumps({"service": service, "subject": subject, "steps": steps, "verdict": walk["verdict"]}, sort_keys=True)
report["trace_digest"] = hashlib.sha256(digest_src.encode()).hexdigest()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
echo "$output"
