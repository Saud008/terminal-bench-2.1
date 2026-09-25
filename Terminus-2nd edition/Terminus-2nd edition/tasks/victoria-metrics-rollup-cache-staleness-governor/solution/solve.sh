#!/usr/bin/env bash
# Oracle solve — task identity victoria-metrics-rollup-cache-staleness-governor token f58d4df5
set -euo pipefail

APP="/app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR=""
for candidate in "${SCRIPT_DIR}/patches" "${SCRIPT_DIR}" "/solution/patches" "/oracle/solution/patches" "/task/solution/patches"; do
  if [ -f "${candidate}/vmrollup_query_serve.oracle" ]; then
    PATCH_DIR="${candidate}"
    break
  fi
done

if [ -z "${PATCH_DIR}" ]; then
  echo "oracle: vmrollup_query_serve.oracle not found under solution/patches" >&2
  exit 1
fi

install -m 0644 "${PATCH_DIR}/vmrollup_cache_entry.oracle" "${APP}/internal/cache/entry.go"
install -m 0644 "${PATCH_DIR}/vmrollup_cache_ttl.oracle" "${APP}/internal/cache/ttl.go"
install -m 0644 "${PATCH_DIR}/vmrollup_counter_reset.oracle" "${APP}/internal/counter/reset.go"
install -m 0644 "${PATCH_DIR}/vmrollup_downsample_tier.oracle" "${APP}/internal/downsample/tier.go"
install -m 0644 "${PATCH_DIR}/vmrollup_histogram_merge.oracle" "${APP}/internal/histogram/merge.go"
install -m 0644 "${PATCH_DIR}/vmrollup_query_serve.oracle" "${APP}/internal/query/serve.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/vmrollup ./cmd/vmrollup
bash "${APP}/scripts/reset-state.sh"
