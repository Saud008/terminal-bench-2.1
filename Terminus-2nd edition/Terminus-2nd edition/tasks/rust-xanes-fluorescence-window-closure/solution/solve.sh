#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR=""
for candidate in "${SCRIPT_DIR}/patches" "/solution/patches" "/oracle/solution/patches"; do
  if [ -f "${candidate}/xanes_mu_window_seal.oracle" ]; then
    PATCH_DIR="${candidate}"
    break
  fi
done
[[ -n "${PATCH_DIR}" ]] || { echo "xanes oracle patches not found" >&2; exit 1; }

DEST="${APP_ROOT}/crates/xanes-core/src"
python3 - "${PATCH_DIR}" "${DEST}" <<'PY'
import shutil
import sys
from pathlib import Path

patch_dir, dest = Path(sys.argv[1]), Path(sys.argv[2])
pairs = {
    "xanes_victoreen_fit.oracle": "victoreen_fit.rs",
    "xanes_edge_ordinal.oracle": "edge_ordinal.rs",
    "xanes_mu_window_seal.oracle": "mu_window_seal.rs",
}
for src_name, dst_name in pairs.items():
    shutil.copyfile(patch_dir / src_name, dest / dst_name)
print("xanes oracle patches applied")
PY

cd "${APP_ROOT}"
/usr/local/cargo/bin/cargo build --locked --release --bin xanesctl
install -m 0755 target/release/xanesctl /usr/local/bin/xanesctl
bash "${APP_ROOT}/scripts/reset-state.sh"
