#!/usr/bin/env bash
# Ingest WAL archive tree into staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/staging.sh"
source "${APP_ROOT}/lib/ingest/helpers.sh"

archive=""
staging=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) archive="$2"; shift 2 ;;
    --staging) staging="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[[ -n "${archive}" && -n "${staging}" ]] || die "ingest requires --archive and --staging"
validate_ingest_paths "${archive}" "${staging}"
write_staging_snapshot "${archive}" "${staging}"
echo "ingested $(basename "${archive}")"
