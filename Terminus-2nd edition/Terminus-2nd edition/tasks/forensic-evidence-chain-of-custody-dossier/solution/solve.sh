#!/usr/bin/env bash
set -euo pipefail
cd /app
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

require_file() {
  local candidate="$1"
  if [[ ! -f "$candidate" ]]; then
    echo "oracle missing patch file: $candidate" >&2
    exit 1
  fi
}

for patch in mod_a mod_b mod_c mod_d mod_e mod_f mod_g; do
  require_file "$ROOT_DIR/files/${patch}.rs"
done

install -m 0644 "$ROOT_DIR/files/mod_a.rs" /app/src/x7k/mod_a.rs
install -m 0644 "$ROOT_DIR/files/mod_b.rs" /app/src/n3p/mod_b.rs
install -m 0644 "$ROOT_DIR/files/mod_c.rs" /app/src/p9w/mod_c.rs
install -m 0644 "$ROOT_DIR/files/mod_d.rs" /app/src/q2r/mod_d.rs
install -m 0644 "$ROOT_DIR/files/mod_e.rs" /app/src/t5m/mod_e.rs
install -m 0644 "$ROOT_DIR/files/mod_f.rs" /app/src/u8j/mod_f.rs
install -m 0644 "$ROOT_DIR/files/mod_g.rs" /app/src/v1z/mod_g.rs

bash /app/scripts/reset-state.sh
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/rvk9 /app/bin/rvk9
test -x /app/bin/rvk9
test -f /app/src/v1z/mod_g.rs

/app/bin/rvk9 vault load --case CASE-METRO-441 --bundle metro-gun-chain
/app/bin/rvk9 registry bind --case CASE-METRO-441 --bundle metro-gun-chain
/app/bin/rvk9 attest dossier --case CASE-METRO-441 --bundle metro-gun-chain --output /app/output/oracle-smoke-dossier.json

test -s /app/output/oracle-smoke-dossier.json
test -s /app/var/custody-vault.json
test -s /app/var/exhibit-register.json
