use crate::growth::append_proof::verify_consistency;
use crate::ctpath::leaf_body::{verify_inclusion, ProofStep};
use crate::ledgerfmt::hex_norm::{
    load_bundles_from_index, load_witness_file, normalize_root, AuditBundle, WitnessCheckpoint,
};
use crate::cosign::chron_order::timestamps_monotonic;
use crate::cosign::vote_tally::{quorum_met, witness_set_hash};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StagedAuditRow {
    pub log_id: String,
    pub older_tree_size: u64,
    pub newer_tree_size: u64,
    pub inclusion_ok: bool,
    pub consistency_ok: bool,
    pub witness_quorum_ok: bool,
    pub timestamp_monotonic_ok: bool,
    pub witness_set_hash: String,
}

fn row_inclusion_flag(bundle: &AuditBundle) -> bool {
    let inc_path = steps_from_json(&bundle.inclusion.audit_path);
    let newer_root = normalize_root(&bundle.newer_sth.sha256_root_hash);
    verify_inclusion(&bundle.inclusion.leaf_input, &newer_root, &inc_path)
}

fn steps_from_json(path: &[crate::ledgerfmt::hex_norm::ProofStepJson]) -> Vec<ProofStep> {
    path.iter()
        .filter_map(|s| {
            let hash = hex::decode(&s.hash).ok()?;
            Some(ProofStep {
                hash,
                side: s.side.clone(),
            })
        })
        .collect()
}

fn evaluate_bundle(bundle: &AuditBundle, checkpoints: &[WitnessCheckpoint]) -> StagedAuditRow {
    let newer_root = normalize_root(&bundle.newer_sth.sha256_root_hash);
    let older_root = normalize_root(&bundle.older_sth.sha256_root_hash);
    let inclusion_ok = row_inclusion_flag(bundle);
    let con_path = steps_from_json(&bundle.consistency.audit_path);
    let consistency_ok = verify_consistency(
        &older_root,
        &newer_root,
        bundle.consistency.from_size,
        bundle.consistency.to_size,
        &con_path,
    );
    let witness_quorum_ok = quorum_met(
        &bundle.log_id,
        bundle.newer_sth.tree_size,
        &newer_root,
        checkpoints,
    );
    let timestamp_monotonic_ok = timestamps_monotonic(
        bundle.older_sth.timestamp,
        bundle.newer_sth.timestamp,
        bundle.older_sth.tree_size,
        bundle.newer_sth.tree_size,
    );
    let wsh = witness_set_hash(
        &bundle.log_id,
        bundle.newer_sth.tree_size,
        &newer_root,
        checkpoints,
    );
    StagedAuditRow {
        log_id: bundle.log_id.clone(),
        older_tree_size: bundle.older_sth.tree_size,
        newer_tree_size: bundle.newer_sth.tree_size,
        inclusion_ok,
        consistency_ok,
        witness_quorum_ok,
        timestamp_monotonic_ok,
        witness_set_hash: wsh,
    }
}

pub fn materialize_checkpoint_rows(index_path: &Path, ledger_path: &Path, staging_path: &Path) -> Result<(), String> {
    let bundles = load_bundles_from_index(index_path).map_err(|_| "bundle discovery failed".to_string())?;
    let checkpoints = load_witness_file(ledger_path).map_err(|_| "witness read failed".to_string())?;
    let mut rows: Vec<StagedAuditRow> = bundles.iter().map(|b| evaluate_bundle(b, &checkpoints)).collect();
    rows.sort_by(|a, b| a.log_id.cmp(&b.log_id));
    let json = serde_json::to_string_pretty(&rows).map_err(|e| e.to_string())?;
    fs::write(staging_path, format!("{json}\n")).map_err(|e| e.to_string())
}

pub fn read_staging_snapshot(path: &Path) -> Result<Vec<StagedAuditRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}



