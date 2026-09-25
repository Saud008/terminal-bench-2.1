#!/usr/bin/env bash
set -euo pipefail

APP="${APP_ROOT:-/app}"
export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SELF")"
sed -i 's/\r$//' "$SELF" 2>/dev/null || true

SOL_DIR=""
for candidate in \
  "/solution" \
  "/oracle/solution" \
  "/task/solution" \
  "${SCRIPT_DIR}" \
  "/tasks/tbench-task/solution"; do
  if [ -f "${candidate}/golden_mount.sh" ] && [ -f "${candidate}/golden_driver.sh" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden module scripts not found" >&2
  exit 1
fi

LIB="${APP}/lib"
cp -f "${SOL_DIR}/golden_mount.sh" "${LIB}/mount.sh"
cp -f "${SOL_DIR}/golden_commit.sh" "${LIB}/commit.sh"
cp -f "${SOL_DIR}/golden_gate.sh" "${LIB}/gate.sh"
cp -f "${SOL_DIR}/golden_hooks.sh" "${LIB}/hooks.sh"
cp -f "${SOL_DIR}/golden_resolv.sh" "${LIB}/resolv.sh"
cp -f "${SOL_DIR}/golden_sources.sh" "${LIB}/sources.sh"
cp -f "${SOL_DIR}/golden_staging.sh" "${LIB}/staging.sh"
cp -f "${SOL_DIR}/golden_export.sh" "${LIB}/export.sh"
cp -f "${SOL_DIR}/golden_driver.sh" "${LIB}/driver.sh"

for f in "${LIB}/"*.sh "${APP}/bin/stage2-audit"; do
  sed -i 's/\r$//' "$f" 2>/dev/null || true
done

chmod +x "${APP}/bin/stage2-audit" "${LIB}/"*.sh "${APP}/scripts/"*.sh
bash "${APP}/scripts/reset-state.sh"

test -x "${APP}/bin/stage2-audit"
SMOKE="/tmp/oracle-smoke.json"
"${APP}/bin/stage2-audit" run \
  --rootfs "${APP}/fixtures/rootfs/rootfs-001" \
  --output "$SMOKE"
test -s "$SMOKE"

echo "stage2-audit oracle ready"
