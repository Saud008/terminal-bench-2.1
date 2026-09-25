#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_DIR="${ROOT}/solution/patches"
mkdir -p "${PATCH_DIR}"
pairs=(
  "pkg/objclock/generator.go:objclock_mint.go"
  "pkg/digestseal/snapshot.go:bson_batch_digest_durastore.go"
  "pkg/oidstore/commit.go:oidstore_persist.go"
  "pkg/intakegate/service.go:http_intake_handler.go"
  "pkg/srcursor/by_path.go:srcursor_by_path.go"
  "pkg/jsonlresume/apply.go:jsonlresume_apply.go"
)
for pair in "${pairs[@]}"; do
  envf="${pair%%:*}"
  oraf="${pair##*:}"
  out="${PATCH_DIR}/$(echo "${envf}" | tr '/' '-').patch"
  tmp="$(mktemp -d)"
  mkdir -p "${tmp}/$(dirname "${envf}")"
  cp "${ROOT}/environment/${envf}" "${tmp}/${envf}"
  cp "${ROOT}/solution/oracle/${oraf}" "${tmp}/${envf}.new"
  diff -u "${tmp}/${envf}" "${tmp}/${envf}.new" | sed "1s|.*|--- ${envf}|; 2s|.*|+++ ${envf}|" > "${out}" || true
  rm -rf "${tmp}"
done
