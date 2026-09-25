#!/usr/bin/env bash
# Reconcile Ansible facts JSONL into facts.db.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/jsonl.sh"
source "${APP_ROOT}/lib/diff.sh"
source "${APP_ROOT}/lib/merge.sh"

jsonl=""
run_id=""
while [ $# -gt 0 ]; do
  case "$1" in
    --jsonl) jsonl="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${jsonl}" ] && [ -n "${run_id}" ] || die "reconcile requires --jsonl and --run-id"

require_file "${jsonl}"
mkdir -p "$(dirname "${FACTS_DB}")"
ensure_facts_schema
ingest_jsonl_file "${jsonl}" "${run_id}"

echo "reconciled $(snapshot_count) fact keys for run ${run_id}"
