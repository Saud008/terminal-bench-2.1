#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

apply_one() {
  local hunk="$1"
  if command -v patch >/dev/null 2>&1; then
    # Use absolute -i path: patch -d chdirs before opening the patch file.
    patch -d /app --forward --strip=0 -i "${ROOT}/${hunk}"
  else
    python3 "${ROOT}/apply_unified_diff.py" /app "${ROOT}/${hunk}"
  fi
}

apply_one patches/fqdn_alias.patch
apply_one patches/reader_default.patch
apply_one patches/branch_set.patch
apply_one patches/logical_check.patch
apply_one patches/canonical_fp.patch
apply_one patches/ledger_ingest.patch
apply_one patches/migration_emit.patch
