#!/usr/bin/env bash
# Oracle: install corrected lib modules from bundled golden sources.
set -euo pipefail

APP="/app"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_text() {
  local src="$1"
  local dest="$2"
  tr -d '\r' < "${src}" > "${dest}"
}

SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_age_eval.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_age_eval.sh not found" >&2
  exit 1
fi

LIB="${APP}/lib"
for golden in "${SOL_DIR}"/golden_*.sh; do
  [ -f "${golden}" ] || continue
  base="$(basename "${golden}")"
  install_text "${golden}" "${LIB}/${base#golden_}"
done

chmod +x "${APP}/bin/tmpfiles-replay" "${LIB}/"*.sh

bash "${APP}/scripts/reset-state.sh"

smoke_apply() {
  local scenario="$1"
  local now_epoch="$2"
  local out="$3"
  if ! "${APP}/bin/tmpfiles-replay" apply \
    --scenario "${scenario}" \
    --seed alpha01 \
    --now "${now_epoch}" \
    --export "${out}"; then
    echo "oracle: smoke apply failed for ${scenario}" >&2
    exit 1
  fi
  if [ ! -s "${out}" ]; then
    echo "oracle: smoke export missing for ${scenario}" >&2
    exit 1
  fi
}

smoke_apply "001-atime-btime-age" 10000 /tmp/oracle-smoke-001.json
smoke_apply "007-combined-trap" 10000 /tmp/oracle-smoke-007.json

SMOKE_GEN="/tmp/oracle-smoke-generate.json"
if ! "${APP}/bin/tmpfiles-replay" generate \
  --scenario 005-boot-ex-merge \
  --mode boot-ex \
  --export-rules "${SMOKE_GEN}"; then
  echo "oracle: smoke generate failed" >&2
  exit 1
fi
if [ ! -s "${SMOKE_GEN}" ]; then
  echo "oracle: smoke generate export missing" >&2
  exit 1
fi

echo "tmpfiles-replay oracle ready"
