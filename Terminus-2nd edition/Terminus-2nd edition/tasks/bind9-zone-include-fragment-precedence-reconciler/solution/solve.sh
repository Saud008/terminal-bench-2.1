# Oracle solve — task identity bind9-zone-include-fragment-precedence-reconciler token 05ed771b
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
  if [ -f "${candidate}/golden_include.sh" ]; then
    SOL="${candidate}"
    break
  fi
done

if [ -z "${SOL}" ]; then
  echo "oracle: golden_include.sh not found" >&2
  exit 1
fi

LIB="${APP}/lib"
GOLDEN_FILES=(
  common.sh:golden_common.sh
  parse.sh:golden_parse.sh
  include.sh:golden_include.sh
  wildcard.sh:golden_wildcard.sh
  serial.sh:golden_serial.sh
  nsec.sh:golden_nsec.sh
  cache.sh:golden_cache.sh
  digest.sh:golden_digest.sh
  order.sh:golden_order.sh
  merge.sh:golden_merge.sh
  staging.sh:golden_staging.sh
  export.sh:golden_export.sh
  compile.sh:golden_compile.sh
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

sed -i 's/\r$//' /app/scripts/zonefrag 2>/dev/null || true
chmod +x /app/scripts/zonefrag "${LIB}/"*.sh /app/scripts/*.sh

bash "${APP}/scripts/reset-state.sh"

test -x /usr/local/bin/zonefrag

SMOKE_OUT="${APP}/output/.oracle-smoke.json"
zonefrag compile \
  --tree "${APP}/fixtures/bundles/layered-precedence" \
  --seed alpha \
  --output "${SMOKE_OUT}"
rm -f "${SMOKE_OUT}"

echo "zonefrag oracle ready"
