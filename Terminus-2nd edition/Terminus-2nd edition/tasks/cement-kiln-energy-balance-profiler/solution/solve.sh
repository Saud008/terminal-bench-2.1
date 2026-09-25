#!/usr/bin/env bash
# Oracle solve — task identity cement-kiln-energy-balance-profiler token c7k9e2f1
set -euo pipefail
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

sed -i 's/raw - 273.0/raw - 273.15/' c7_u9norm/convert.rs
sed -i 's/mass_kg \* cv_kcal_kg \* 4.184/mass_kg * cv_kcal_kg * kcal_to_mj/' c7_u9norm/convert.rs
sed -i 's/temp_norm_c + cal_offset_c/temp_norm_c - cal_offset_c/' c7_p4bias/apply.rs
sed -i 's/ts > b.start_ts && ts < b.end_ts/ts >= b.start_ts \&\& ts <= b.end_ts/' c7_f2bind/map.rs
sed -i 's/energy_in_mj - clinker_energy_mj + heat_loss_mj/energy_in_mj - clinker_energy_mj - heat_loss_mj/' c7_h3score/score.rs

cat > c7_g5span/interp.rs <<'ORACLE_EOF'
use crate::types::ProbeWindow;

pub fn fill_gaps(
    points: Vec<(u64, String, f64)>,
    grid_step: u64,
    batch_lookup: &dyn Fn(u64) -> Option<String>,
) -> Vec<ProbeWindow> {
    if points.is_empty() {
        return Vec::new();
    }
    let mut uniq = points;
    uniq.sort_by_key(|p| p.0);
    let min_ts = uniq.first().unwrap().0;
    let max_ts = uniq.last().unwrap().0;
    let mut out = Vec::new();
    let mut ts = min_ts;
    while ts <= max_ts {
        let exact = uniq.iter().find(|p| p.0 == ts);
        let (temp_c, pid, interpolated) = if let Some((_, id, v)) = exact {
            (*v, id.clone(), false)
        } else {
            let lower = uniq.iter().rev().find(|p| p.0 < ts);
            let upper = uniq.iter().find(|p| p.0 > ts);
            match (lower, upper) {
                (Some(l), Some(u)) => {
                    let frac = (ts - l.0) as f64 / (u.0 - l.0) as f64;
                    let v = l.2 + frac * (u.2 - l.2);
                    (v, l.1.clone(), true)
                }
                _ => {
                    ts += grid_step;
                    continue;
                }
            }
        };
        let batch_id = batch_lookup(ts).unwrap_or_default();
        out.push(ProbeWindow {
            probe_ts: ts,
            probe_id: pid,
            temp_c,
            batch_id,
            interpolated,
        });
        ts += grid_step;
    }
    out
}
ORACLE_EOF

cat > c7_l8emit/write.rs <<'ORACLE_EOF'
use crate::types::{BalanceScratch, FuelBatch, HeatBalanceLedger, ProbeWindow};
use sha2::{Digest, Sha256};

pub fn lineage_digest(_fuels: &[FuelBatch], probes: &[ProbeWindow]) -> String {
    let mut pairs: Vec<String> = probes
        .iter()
        .map(|p| format!("{}:{}", p.probe_ts, p.batch_id))
        .collect();
    pairs.sort();
    hex::encode(Sha256::digest(pairs.join("|").as_bytes()))
}

pub fn audit_digest(ledger: &HeatBalanceLedger) -> String {
    let body = serde_json::json!({
        "clinker_out_t": ledger.clinker_out_t,
        "energy_in_mj": ledger.energy_in_mj,
        "heat_loss_mj": ledger.heat_loss_mj,
        "lineage_digest": ledger.lineage_digest,
        "residual_mj_per_t": ledger.residual_mj_per_t,
        "run_id": ledger.run_id,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_ledger(
    run_id: &str,
    kiln_id: &str,
    scratch: &BalanceScratch,
    fuels: Vec<FuelBatch>,
    probes: Vec<ProbeWindow>,
) -> HeatBalanceLedger {
    let lin = lineage_digest(&fuels, &probes);
    let mut ledger = HeatBalanceLedger {
        run_id: run_id.to_string(),
        kiln_id: kiln_id.to_string(),
        energy_in_mj: scratch.energy_in_mj,
        clinker_out_t: scratch.clinker_out_t,
        heat_loss_mj: scratch.heat_loss_mj,
        residual_mj: scratch.residual_mj,
        residual_mj_per_t: scratch.residual_mj_per_t,
        fuel_batches: fuels,
        probe_windows: probes,
        lineage_digest: lin,
        audit_digest: String::new(),
    };
    ledger.audit_digest = audit_digest(&ledger);
    ledger
}
ORACLE_EOF


/usr/local/cargo/bin/cargo generate-lockfile
/usr/local/cargo/bin/cargo build --release --locked
test -x /app/target/release/kilnbal
install -m 0755 /app/target/release/kilnbal /app/bin/kilnbal

bash /app/scripts/reset-workspace.sh
/app/bin/kilnbal load-probes --run-id oracle-smoke --telemetry /app/fixtures/kiln-runs/kiln-run-01/telemetry.csv
/app/bin/kilnbal bind-fuel --run-id oracle-smoke --fuel /app/fixtures/kiln-runs/kiln-run-01/fuel.csv --clinker /app/fixtures/kiln-runs/kiln-run-01/clinker.csv --kiln-id K7
/app/bin/kilnbal interpolate-probes --run-id oracle-smoke
/app/bin/kilnbal score-balance --run-id oracle-smoke --heat-loss /app/fixtures/kiln-runs/kiln-run-01/heat_loss.json
/app/bin/kilnbal publish-ledger --run-id oracle-smoke --output /app/output/oracle-smoke-heat-balance-ledger.json
test -s /app/output/oracle-smoke-heat-balance-ledger.json
test -s /app/work/probe-grid/oracle-smoke.json
test -s /app/state/tele-buffer/oracle-smoke.jsonl
test -s /app/work/fuel-buffer/oracle-smoke.json

python3 - <<'PY'
import json
from pathlib import Path

ledger = json.loads(Path("/app/output/oracle-smoke-heat-balance-ledger.json").read_text())
assert ledger["run_id"] == "oracle-smoke"
assert ledger["energy_in_mj"] > 0
assert ledger["probe_windows"]
assert ledger["lineage_digest"]
assert ledger["audit_digest"]
assert ledger["residual_mj_per_t"] != 0.0
grid = json.loads(Path("/app/work/probe-grid/oracle-smoke.json").read_text())
assert len(grid) >= 1
PY
