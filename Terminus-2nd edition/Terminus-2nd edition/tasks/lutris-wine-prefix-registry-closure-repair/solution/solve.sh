#!/usr/bin/env bash
# Self-normalize CRLF before set -e (/solution is often read-only on the platform).
if grep -q $'\r' "$0" 2>/dev/null; then
  _solve_tmp="$(mktemp)"
  sed 's/\r$//' "$0" >"${_solve_tmp}"
  chmod +x "${_solve_tmp}"
  exec bash "${_solve_tmp}" "$@"
fi
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/bin:/usr/bin:/bin:${PATH}"
cd "${APP_ROOT}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}" \
  "/solution" \
  "/oracle/solution" \
  "/oracle" \
  "/task/solution"; do
  if [ -f "${candidate}/golden_registry.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden_registry.sh not found" >&2
  exit 1
fi

install_golden() {
  local src="$1"
  local dst="$2"
  sed 's/\r$//' "${src}" >"${dst}"
}

install_golden "${SOL_DIR}/golden_registry.sh" "${APP_ROOT}/lib/registry.sh"
install_golden "${SOL_DIR}/golden_closure.sh" "${APP_ROOT}/lib/closure.sh"
install_golden "${SOL_DIR}/golden_prefix.sh" "${APP_ROOT}/lib/prefix.sh"
install_golden "${SOL_DIR}/golden_semver.sh" "${APP_ROOT}/lib/semver.sh"

for lib_sh in "${APP_ROOT}/lib/"*.sh; do
  sed -i 's/\r$//' "${lib_sh}"
done
chmod +x "${APP_ROOT}/lib/"*.sh

bash "${APP_ROOT}/scripts/reset-state.sh"

/usr/local/bin/lutris-resolve resolve \
  --registry-dir "${APP_ROOT}/fixtures/registry/001-transitive-runner" \
  --root-slug frontier-rpg \
  --output "${APP_ROOT}/output/oracle-smoke.json"
