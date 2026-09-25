#!/usr/bin/env bash
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
  if [ -f "${candidate}/golden_spool.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_spool.sh not found" >&2
  exit 1
fi

LIB="${APP}/lib"
for golden in "${SOL_DIR}"/golden_*.sh; do
  [ -f "${golden}" ] || continue
  base="$(basename "${golden}")"
  install_text "${golden}" "${LIB}/${base#golden_}"
done

chmod +x "${APP}/bin/at-replay" "${LIB}/"*.sh

bash "${APP}/scripts/reset-state.sh"

SMOKE_OUT="/tmp/oracle-smoke.json"
if ! "${APP}/bin/at-replay" replay \
  --scenario 001-basic-due \
  --seed alpha01 \
  --clock 1700000000 \
  --export "${SMOKE_OUT}"; then
  echo "oracle: smoke replay failed" >&2
  exit 1
fi
if [ ! -s "${SMOKE_OUT}" ]; then
  echo "oracle: smoke export missing" >&2
  exit 1
fi

echo "at-replay oracle ready"
