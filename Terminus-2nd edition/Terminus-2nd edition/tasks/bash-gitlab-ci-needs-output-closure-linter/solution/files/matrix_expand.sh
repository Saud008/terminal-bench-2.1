#!/usr/bin/env bash
set -euo pipefail

matrix_expand_name() {
  local base="$1"
  local row_json="$2"
  local suffix=""
  local key
  for key in $(echo "$row_json" | jq -r 'keys[]' | sort); do
    local val
    val=$(echo "$row_json" | jq -r --arg k "$key" '.[$k]')
    suffix="${suffix}/${key}=${val}"
  done
  echo "${base}${suffix}"
}

expand_matrix_jobs() {
  local pipeline_json="$1"
  python3 - <<'PY' "$pipeline_json"
import json, sys
pipeline = json.loads(sys.argv[1])
out = []
for name, job in pipeline.items():
    if name in ("stages", "variables", "default", "include", "workflow"):
        continue
    if not isinstance(job, dict):
        continue
    par = job.get("parallel")
    if isinstance(par, dict) and "matrix" in par:
        for row in par["matrix"]:
            out.append({"base": name, "matrix_row": row})
    else:
        out.append({"base": name, "matrix_row": None})
print(json.dumps(out))
PY
}
