#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_ROOT=""

for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files"; do
  if [ -f "${candidate}/module_map.json" ]; then
    FILES_ROOT="${candidate}"
    break
  fi
done

[[ -n "${FILES_ROOT}" ]] || { echo "oracle: module_map.json not found" >&2; exit 1; }

python3 "${SCRIPT_DIR}/apply_lib_modules.py" \
  --files-root "${FILES_ROOT}" \
  --app-root "${APP_ROOT}"

find "${APP_ROOT}/lib" -type f -name '*.sh' -exec sed -i 's/\r$//' {} +

bash "${APP_ROOT}/scripts/reset-state.sh"
"${APP_ROOT}/bin/demo-index" build \
  --root "${APP_ROOT}/fixtures/demos" \
  --seed primary01 \
  --out "${APP_ROOT}/output/tick-index.json"
