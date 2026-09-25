#!/usr/bin/env bash
# Export facts-diff.json report for a reconcile run.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/diff.sh"

run_id=""
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${run_id}" ] && [ -n "${out}" ] || die "export requires --run-id and --out"

[ -f "${FACTS_DB}" ] || die "run reconcile before export"
[ -f "${STAGING_JSON}" ] || die "missing staging snapshot: ${STAGING_JSON}"

changed="$(export_changed_key_count "${run_id}")"
digest="$(export_changed_keys_digest "${run_id}")"
rows="$(export_diff_rows_json "${run_id}")"

python3 - "${out}" "${run_id}" "${changed}" "${digest}" "${rows}" <<'PY'
import json, sys
out, run_id, changed, digest, rows = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
doc = {
    "run_id": run_id,
    "changed_key_count": changed,
    "changed_keys_digest": digest,
    "diff_rows": json.loads(rows),
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "exported ${out}"
