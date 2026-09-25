#!/usr/bin/env bash
# Oracle solve — substation-switching-order-interlock-checker
# Installs corrected Rust modules by file copy (no patch(1) dependency).
set -euo pipefail

cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT=""
for candidate in "${SCRIPT_DIR}/files" "/solution/files" "/oracle/solution/files"; do
  if [ -f "${candidate}/seq_anchor.rs" ]; then
    PATCH_ROOT="${candidate}"
    break
  fi
done
[[ -n "${PATCH_ROOT}" ]] || { echo "oracle patch files not found" >&2; exit 1; }

install_patch() {
  local name="$1"
  local src="${PATCH_ROOT}/${name}"
  local dest="/app/src/${name}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  install -m 0644 "${src}" "${dest}"
  sed -i 's/\r$//' "${dest}" 2>/dev/null || true
}

install_patch seq_anchor.rs
install_patch loto_enforce.rs
install_patch mux_isolation.rs
install_patch proc_walk.rs
install_patch diag_emit.rs

export PATH="/app/bin:/usr/local/cargo/bin:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/relayctl /app/bin/relayctl

bash /app/scripts/reset-state.sh
/app/bin/relayctl compile-yard --seed oracle-smoke --scenario basic-isolation
/app/bin/relayctl verify-order --seed oracle-smoke --scenario basic-isolation --output /app/output/verify-report.json
echo "sublock oracle ready"
