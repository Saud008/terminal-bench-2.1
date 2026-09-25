#!/usr/bin/env bash
# Self-normalize CRLF before set -e (/solution is often read-only on the platform).
if grep -q $'\r' "$0" 2>/dev/null; then
  _solve_tmp="$(mktemp)"
  sed 's/\r$//' "$0" >"${_solve_tmp}"
  chmod +x "${_solve_tmp}"
  exec bash "${_solve_tmp}" "$@"
fi
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution/files" "/oracle/solution" "/task/solution/files" "/task/solution"; do
  if [[ -f "${candidate}/golden_catalog.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_catalog.rs not found" >&2; exit 1; }

install_golden() {
  local src="$1"
  local dst="$2"
  sed 's/\r$//' "${src}" >"${dst}"
}

install_golden "${SOL_DIR}/golden_catalog.rs" /app/crates/atlaspack-core/src/catalog.rs
install_golden "${SOL_DIR}/golden_pack.rs" /app/crates/atlaspack-core/src/pack.rs
install_golden "${SOL_DIR}/golden_uv.rs" /app/crates/atlaspack-core/src/uv.rs
install_golden "${SOL_DIR}/golden_manifest.rs" /app/crates/atlaspack-core/src/manifest.rs
install_golden "${SOL_DIR}/golden_atlas.rs" /app/crates/atlaspack-core/src/atlas.rs
install_golden "${SOL_DIR}/golden_main.rs" /app/crates/atlaspack/src/main.rs

cargo build --release --locked -p atlaspack
install -m 0755 /app/target/release/atlaspack /usr/local/bin/atlaspack
test -x /usr/local/bin/atlaspack
bash /app/scripts/reset-state.sh
