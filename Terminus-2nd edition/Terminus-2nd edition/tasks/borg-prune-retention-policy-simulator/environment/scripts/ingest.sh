#!/usr/bin/env bash
# Ingest borg list fixture into staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/staging/io.sh"
source "${APP_ROOT}/lib/parse_list.sh"

list_file=""
repo_id=""
while [ $# -gt 0 ]; do
  case "$1" in
    --list) list_file="$2"; shift 2 ;;
    --repo-id) repo_id="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${list_file}" ] && [ -n "${repo_id}" ] || die "ingest requires --list and --repo-id"
require_file "${list_file}"

archives_json="$(parse_list_to_json "${list_file}")"
stage="$(stage_path_for "${list_file}")"
mkdir -p "$(dirname "${stage}")"

python3 - "${stage}" "${repo_id}" "${archives_json}" <<'PY'
import json, sys
out, repo_id, archives_json = sys.argv[1], sys.argv[2], sys.argv[3]
archives = json.loads(archives_json)
doc = {"archives": archives, "repo_id": repo_id}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "ingested ${stage}"
