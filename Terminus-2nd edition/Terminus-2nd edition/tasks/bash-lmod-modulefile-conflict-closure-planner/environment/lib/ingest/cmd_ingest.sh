#!/bin/bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/ingest/ingest_catalog.sh"

catalog=""
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --catalog) catalog="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "${catalog}" && -n "${out}" ]] || { echo "need --catalog and --out" >&2; exit 2; }

declare -a records=()
parse_catalog_dir "${catalog}" records
mkdir -p "$(dirname "${out}")"
write_catalog_snapshot "${out}" "${records[@]}"
