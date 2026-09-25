#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/pk87/matrix/matrix_expand.sh"
source "${APP_ROOT}/internal/pk87/rules/rules_eval.sh"

pipeline="${TB3_PIPELINE_DIR:-${APP_ROOT}/fixtures/pipelines}"
pipeline_name=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pipeline) pipeline_name="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$pipeline_name" && -n "$run_id" ]] || exit 2

yaml_path="${pipeline}/${pipeline_name}.yml"
raw=$(python3 "${APP_ROOT}/internal/pk87/yaml_load.py" "$yaml_path")
mkdir -p "${APP_ROOT}/work"
echo "$raw" > "${APP_ROOT}/work/${run_id}-ingest.json"
echo "ingested ${pipeline_name} for ${run_id}"
