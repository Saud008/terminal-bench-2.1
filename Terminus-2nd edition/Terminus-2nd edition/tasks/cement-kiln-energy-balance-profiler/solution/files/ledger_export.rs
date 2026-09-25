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
