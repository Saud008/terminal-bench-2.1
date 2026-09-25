#!/usr/bin/env bash
set -euo pipefail
S3LC_LIB="${S3LC_LIB:-/app/lib}"
source "${S3LC_LIB}/common.sh"
source "${S3LC_LIB}/inventory/inventory_loader.sh"

write_ingest_staging() {
  local inv="$1" bucket="$2" out="$3"
  ensure_runtime_dirs
  load_inventory_jsonl "$inv" "$bucket" > "$out"
  echo "S3LC:INGEST_OK"
}
