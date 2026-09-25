# Oracle solve — task identity orchard-irrigation-deficit-optimizer token ca9cd43f
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app/environment

install -D -m 0644 "$ROOT_DIR/files/probe_cal_calibration.rs" sfield_kappa/kappa.rs
install -D -m 0644 "$ROOT_DIR/files/unit_depth_convert.rs" sfield_theta/theta.rs
install -D -m 0644 "$ROOT_DIR/files/crop_kc_lookup.rs" sfield_lambda/lambda.rs
install -D -m 0644 "$ROOT_DIR/files/probe_blend_blend.rs" sfield_sigma/sigma.rs
install -D -m 0644 "$ROOT_DIR/files/et_deficit_score.rs" sfield_rho/rho.rs
install -D -m 0644 "$ROOT_DIR/files/quota_roll_carryover.rs" sfield_phi/phi.rs
install -D -m 0644 "$ROOT_DIR/files/pump_cap_capacity.rs" sfield_omega/omega.rs

cargo fmt --all 2>/dev/null || true
cargo build --release
test -x target/release/veldt-cli
install -m 0755 target/release/veldt-cli /app/bin/veldt-cli

mkdir -p /app/output /app/state /app/work
bash /app/scripts/reset-state.sh
/app/bin/veldt-cli load-pack --orchard twin-field-basic --run-id oracle-smoke
/app/bin/veldt-cli build-ledger --run-id oracle-smoke
test -s /app/state/moisture-ledger.json
/app/bin/veldt-cli publish-plan --run-id oracle-smoke --output /app/output/oracle-smoke.json
test -s /app/output/oracle-smoke.json

python3 - <<'PY'
import json
from pathlib import Path
plan = json.loads(Path("/app/output/oracle-smoke.json").read_text())
assert plan["run_id"] == "oracle-smoke"
assert plan["summary"]["assignment_count"] >= 1
assert len(plan["assignments"]) >= 1
ledger = json.loads(Path("/app/state/moisture-ledger.json").read_text())
assert ledger["run_id"] == "oracle-smoke"
assert "ledger_digest" in ledger
PY
