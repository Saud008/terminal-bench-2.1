# Oracle solve — task identity fishery-quota-landing-reconciliation-map token fqlrec7a
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app/environment

install -D -m 0644 "$ROOT_DIR/files/k7_resolver.rs" src/taxon/k7_resolver.rs
install -D -m 0644 "$ROOT_DIR/files/w3_coeff.rs" src/weight/w3_coeff.rs
install -D -m 0644 "$ROOT_DIR/files/m2_gate.rs" src/policy/m2_gate.rs
install -D -m 0644 "$ROOT_DIR/files/z9_zone.rs" src/policy/z9_zone.rs
install -D -m 0644 "$ROOT_DIR/files/r4_ledger.rs" src/policy/r4_ledger.rs
install -D -m 0644 "$ROOT_DIR/files/quota_atlas.rs" src/atlas/quota_atlas.rs

cargo fmt --all 2>/dev/null || true
cargo build --release
test -x target/release/fqrctl
install -m 0755 target/release/fqrctl /app/bin/fqrctl

mkdir -p /app/output /app/var
bash /app/scripts/reset-var.sh
/app/bin/fqrctl --season twin-vessel-basic --token oracle-smoke --dest /app/output/oracle-smoke.json
test -s /app/var/quota-ledger-oracle-smoke.jsonl
test -s /app/output/oracle-smoke.json

python3 - <<'PY'
import json
from pathlib import Path

body = json.loads(Path("/app/output/oracle-smoke.json").read_text())
assert body["run_token"] == "oracle-smoke"
assert body["summary"]["species_tracks"] >= 1
assert body["species_rows"]
assert body["landing_audit"]
assert "atlas_fingerprint" in body

hdr = json.loads(Path("/app/var/quota-ledger-oracle-smoke.header.json").read_text())
assert hdr["run_token"] == "oracle-smoke"
assert hdr["row_count"] == len(body["landing_audit"])
assert "ledger_fingerprint" in hdr

lines = Path("/app/var/quota-ledger-oracle-smoke.jsonl").read_text().strip().splitlines()
assert len(lines) == hdr["row_count"]
for line in lines:
    row = json.loads(line)
    assert "species_resolved" in row
    assert "accepted" in row
PY
