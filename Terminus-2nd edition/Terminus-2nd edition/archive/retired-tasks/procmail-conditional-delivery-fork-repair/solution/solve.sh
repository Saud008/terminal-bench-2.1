#!/usr/bin/env bash
set -euo pipefail

APP="/app"
export PATH="/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sed -i 's/\r$//' "${SCRIPT_DIR}/solve.sh" 2>/dev/null || true

SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [ -d "${candidate}/golden_lib/procmail-sim" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_lib/procmail-sim not found" >&2; exit 1; }

if [ ! -e /solution/solve.sh ]; then
  mkdir -p /solution
  ln -sf "${SCRIPT_DIR}/solve.sh" /solution/solve.sh 2>/dev/null || cp "${SCRIPT_DIR}/solve.sh" /solution/solve.sh
fi

DEST="${APP}/lib/procmail-sim"
mkdir -p "${DEST}"
for golden in "${SOL}/golden_lib/procmail-sim/"*.sh; do
  install -m 0755 "${golden}" "${DEST}/$(basename "${golden}")"
  sed -i 's/\r$//' "${DEST}/$(basename "${golden}")"
done

chmod +x "${APP}/bin/procmail-sim"
bash "${APP}/scripts/reset-state.sh"
echo "procmail-sim oracle ready"
