#!/usr/bin/env bash
# Refresh workshop-plan library scripts before pytest (bash stacks).

set -euo pipefail
ROOT="/app"
for script in "${ROOT}/lib/"*.sh "${ROOT}/ingest/"*.sh; do
  [[ -f "${script}" ]] || continue
  sed -i 's/\r$//' "${script}"
  chmod +x "${script}"
done
chmod +x "${ROOT}/bin/workshop-plan" "${ROOT}/scripts/"*.sh
