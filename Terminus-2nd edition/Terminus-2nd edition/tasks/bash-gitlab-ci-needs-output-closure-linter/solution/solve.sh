#!/usr/bin/env bash
set -euo pipefail
cd /app

# Matrix key ordering fix (small targeted edit, not whole-file rewrite).
sed -i "s/jq -r 'keys\[\]'/jq -r 'keys[]' | sort/" /app/internal/pk87/matrix/matrix_expand.sh
bash -n /app/internal/pk87/matrix/matrix_expand.sh

cat > /app/internal/pk87/rules/rules_eval.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
# Evaluate GitLab rules blocks for a job.
set -euo pipefail

rules_pick_when() {
  local rules_json="$1"
  local when_val="on_success"
  local rule
  # Stop evaluating after the first matching rule.
  while IFS= read -r rule; do
    [[ -z "$rule" ]] && continue
    when_val=$(echo "$rule" | jq -r '.when // "on_success"')
    break
  done < <(echo "$rules_json" | jq -c '.[]?')
  echo "$when_val"
}

rules_job_active() {
  local when_val="$1"
  case "$when_val" in
    never) echo "false" ;;
    *) echo "true" ;;
  esac
}

:
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/rules/rules_eval.sh
bash -n /app/internal/pk87/rules/rules_eval.sh

cat > /app/internal/pk87/needs/stage_order.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

stage_index() {
  local stages_json="$1"
  local stage="$2"
  echo "$stages_json" | jq -r --arg s "$stage" 'index($s) // -1'
}

needs_stage_ok() {
  local stages_json="$1"
  local consumer_stage="$2"
  local producer_stage="$3"
  local ci pi
  ci=$(stage_index "$stages_json" "$consumer_stage")
  pi=$(stage_index "$stages_json" "$producer_stage")
  # Consumer stage index must be strictly greater than producer stage index.
  if (( ci > pi )); then
    return 0
  fi
  return 1
}
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/needs/stage_order.sh
bash -n /app/internal/pk87/needs/stage_order.sh

cat > /app/internal/pk87/needs/needs_graph.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

parse_needs() {
  local needs_json="$1"
  echo "$needs_json" | jq -c '
    if . == null then []
    elif type == "string" then [{job: ., optional: false}]
    elif type == "array" then
      map(if type == "string" then {job: ., optional: false}
          else {job: .job, optional: (.optional // false), artifacts: (.artifacts // false)} end)
    else [] end'
}

# Optional need edges carry artifacts flags into staging needs records.
need_is_optional() {
  local edge="$1"
  echo "$edge" | jq -r '.optional // false'
}
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/needs/needs_graph.sh
bash -n /app/internal/pk87/needs/needs_graph.sh

cat > /app/internal/pk87/staging/staging_writer.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
# Staging digest covers run_id, active job shape, and rules fingerprint.
set -euo pipefail

staging_digest() {
  local body_json="$1"
  python3 - <<'PY' "$body_json"
import hashlib, json, sys
body = json.loads(sys.argv[1])
slim = {
    "run_id": body["run_id"],
    "jobs": [{"name": j["name"], "stage": j["stage"], "active": j["active"]} for j in body["jobs"]],
    "rules_fingerprint": body.get("rules_fingerprint", ""),
}
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
}
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/staging/staging_writer.sh
bash -n /app/internal/pk87/staging/staging_writer.sh

cat > /app/internal/pk87/analyze/analyze_stage.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
# Analyze materializes gclint-staging.json from ingest work artifacts.
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/pk87/matrix/matrix_expand.sh"
source "${APP_ROOT}/internal/pk87/rules/rules_eval.sh"
source "${APP_ROOT}/internal/pk87/needs/stage_order.sh"
source "${APP_ROOT}/internal/pk87/needs/needs_graph.sh"
source "${APP_ROOT}/internal/pk87/staging/staging_writer.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2

ingest="${APP_ROOT}/work/${run_id}-ingest.json"
pipeline=$(cat "$ingest")
stages=$(echo "$pipeline" | jq -c '.stages // []')

jobs_json="[]"
names_seen="[]"
rules_parts=""
while IFS= read -r item; do
  base=$(echo "$item" | jq -r '.base')
  row=$(echo "$item" | jq -c '.matrix_row')
  if [[ "$row" == "null" ]]; then
    jname="$base"
  else
    jname=$(matrix_expand_name "$base" "$row")
  fi
  if echo "$names_seen" | jq -e --arg n "$jname" 'index($n) != null' >/dev/null; then
    dup=true
  else
    dup=false
    names_seen=$(echo "$names_seen" | jq --arg n "$jname" '. + [$n]')
  fi
  job_def=$(echo "$pipeline" | jq --arg b "$base" '.[$b]')
  stage=$(echo "$job_def" | jq -r '.stage // "test"')
  rules=$(echo "$job_def" | jq -c '.rules // []')
  when_val=$(rules_pick_when "$rules")
  active=$(rules_job_active "$when_val")
  if [[ "$active" == "true" ]]; then
    if [[ -n "$rules_parts" ]]; then rules_parts="${rules_parts}|"; fi
    rules_parts="${rules_parts}${jname}:${when_val}"
  fi
  needs=$(parse_needs "$(echo "$job_def" | jq -c '.needs // null')")
  paths=$(echo "$job_def" | jq -c '(.artifacts.paths // [])')
  jobs_json=$(echo "$jobs_json" | jq \
    --arg name "$jname" --arg stage "$stage" --arg when "$when_val" --arg active "$active" \
    --argjson needs "$needs" --argjson dup "$dup" --argjson paths "$paths" \
    '. + [{name: $name, stage: $stage, when: $when, active: ($active == "true"), needs: $needs, duplicate: $dup, artifacts: {paths: $paths}}]')
done < <(expand_matrix_jobs "$pipeline" | jq -c '.[]')

rules_hash=$(echo -n "$rules_parts" | sha256sum | awk '{print $1}')
body=$(jq -n --arg run_id "$run_id" --argjson jobs "$jobs_json" --arg rules_fp "$rules_hash" \
  --argjson stages "$stages" \
  '{run_id: $run_id, jobs: $jobs, rules_fingerprint: $rules_fp, stages: $stages}')
digest=$(staging_digest "$body")
echo "$body" | jq --arg d "$digest" '. + {staging_digest: $d}' > "${APP_ROOT}/state/gclint-staging.json"
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/analyze/analyze_stage.sh
bash -n /app/internal/pk87/analyze/analyze_stage.sh

cat > /app/internal/pk87/export/export_lint.sh <<'GCLINT_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
# Export reads staging snapshot only for findings assembly.
source "${APP_ROOT}/internal/pk87/needs/stage_order.sh"
source "${APP_ROOT}/internal/pk87/needs/needs_graph.sh"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$output" ]] || exit 2

staging="${APP_ROOT}/state/gclint-staging.json"
snap=$(cat "$staging")
stages=$(echo "$snap" | jq -c '.stages // []')
jobs=$(echo "$snap" | jq -c '.jobs // []')

findings="[]"
# duplicate matrix
while IFS= read -r job; do
  name=$(echo "$job" | jq -r '.name')
  if [[ "$(echo "$job" | jq -r '.duplicate')" == "true" ]]; then
    findings=$(echo "$findings" | jq --arg n "$name" \
      '. + [{code:"MATRIX_DUPLICATE",severity:"error",job:$n,message:"duplicate matrix expansion"}]')
  fi
done < <(echo "$jobs" | jq -c '.[]')

# stage order + missing needs
while IFS= read -r job; do
  active=$(echo "$job" | jq -r '.active')
  [[ "$active" != "true" ]] && continue
  jname=$(echo "$job" | jq -r '.name')
  jstage=$(echo "$job" | jq -r '.stage')
  while IFS= read -r edge; do
    [[ -z "$edge" ]] && continue
    opt=$(echo "$edge" | jq -r '.optional // false')
    [[ "$opt" == "true" ]] && continue
    need=$(echo "$edge" | jq -r '.job')
    prod=$(echo "$jobs" | jq -c --arg n "$need" '.[] | select(.name==$n)')
    if [[ -z "$prod" ]]; then
      findings=$(echo "$findings" | jq --arg j "$jname" --arg n "$need" \
        '. + [{code:"NEED_MISSING",severity:"error",job:$j,message:("missing need "+$n)}]')
      continue
    fi
    pstage=$(echo "$prod" | jq -r '.stage')
    if ! needs_stage_ok "$stages" "$jstage" "$pstage"; then
      findings=$(echo "$findings" | jq --arg j "$jname" --arg n "$need" \
        '. + [{code:"STAGE_ORDER",severity:"error",job:$j,message:("need "+$n+" stage order violation")}]')
    fi
  done < <(echo "$job" | jq -c '.needs[]?')
done < <(echo "$jobs" | jq -c '.[]')

findings=$(python3 - <<'PY' "$findings")
import hashlib, json, sys
findings = json.loads(sys.argv[1])
findings.sort(key=lambda f: (f["job"], f["code"]))
summary = {"error": 0, "warn": 0, "info": 0}
for f in findings:
    summary[f["severity"]] = summary.get(f["severity"], 0) + 1
audit = hashlib.sha256(json.dumps({"codes": [f["code"] for f in findings], "summary": summary}, sort_keys=True).encode()).hexdigest()
print(json.dumps({"findings": findings, "summary": summary, "audit_digest": audit}))
PY

err=$(echo "$findings" | jq -r '.summary.error')
warn=$(echo "$findings" | jq -r '.summary.warn')
info=$(echo "$findings" | jq -r '.summary.info')
audit=$(echo "$findings" | jq -r '.audit_digest')
findings=$(echo "$findings" | jq -c '.findings')

jq -n --arg run_id "$run_id" --argjson findings "$findings" \
  --argjson summary "$(jq -n --argjson e "$err" --argjson w "$warn" --argjson i "$info" '{error:$e,warn:$w,info:$i}')" \
  --arg audit "$audit" \
  '{run_id:$run_id,findings:$findings,summary:$summary,audit_digest:$audit}' > "$output"
GCLINT_ORACLE_EOF
chmod +x /app/internal/pk87/export/export_lint.sh
bash -n /app/internal/pk87/export/export_lint.sh

bash /app/scripts/rebuild-gclint.sh
bash /app/scripts/reset-state.sh

/app/bin/gclint ingest --pipeline matrix-basic --run-id oracle-smoke >/dev/null
/app/bin/gclint analyze --run-id oracle-smoke >/dev/null
test -s /app/state/gclint-staging.json
/app/bin/gclint export --run-id oracle-smoke --output /app/output/oracle-smoke.json >/dev/null
test -s /app/output/oracle-smoke.json
