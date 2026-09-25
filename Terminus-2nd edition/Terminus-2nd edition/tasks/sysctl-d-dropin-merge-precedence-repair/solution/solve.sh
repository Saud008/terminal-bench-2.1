#!/usr/bin/env bash
# Oracle: install corrected lib modules from bundled golden sources (offline; G-025).
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

APP="/app"
export PATH="/usr/local/bin:/usr/bin:/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SOL=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_parse.sh" ]; then
    SOL="${candidate}"
    break
  fi
done

if [ -z "${SOL}" ]; then
  echo "oracle: golden_parse.sh not found" >&2
  exit 1
fi

LIB="${APP}/lib"
GOLDEN_FILES=(
  parse.sh:golden_parse.sh
  normalize.sh:golden_normalize.sh
  digest.sh:golden_digest.sh
  order.sh:golden_order.sh
  layers.sh:golden_layers.sh
  tree.sh:golden_tree.sh
  merge.sh:golden_merge.sh
  export.sh:golden_export.sh
  staging.sh:golden_staging.sh
  replay.sh:golden_replay.sh
  guard.sh:golden_guard.sh
)

for pair in "${GOLDEN_FILES[@]}"; do
  dest="${pair%%:*}"
  src="${pair##*:}"
  src_path="${SOL}/${src}"
  [ -f "${src_path}" ] || {
    echo "oracle: missing ${src_path}" >&2
    exit 1
  }
  tr -d '\r' < "${src_path}" > "${LIB}/${dest}"
done

sed -i 's/\r$//' "${APP}/bin/sysctlmerge" 2>/dev/null || true
chmod +x "${APP}/bin/sysctlmerge" "${LIB}/"*.sh "${APP}/scripts/"*.sh

bash "${APP}/scripts/reset-state.sh"

test -x /usr/local/bin/sysctlmerge

SMOKE_OUT="${APP}/output/.oracle-smoke.json"
sysctlmerge apply \
  --tree "${APP}/fixtures/bundles/layered-precedence" \
  --seed base \
  --output "${SMOKE_OUT}"
rm -f "${SMOKE_OUT}"

echo "sysctlmerge oracle ready"
