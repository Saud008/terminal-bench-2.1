use std::fs;

use crate::crypto::quorum;
use crate::ledger::provenance;
use crate::types::{StagingDoc, VerifyResult};

pub fn eval_quorum_at_epoch(staging_path: &str, epoch: u64, verdict_path: &str) -> Result<(), String> {
    let staging: StagingDoc = read_json(staging_path)?;
    let outcomes = quorum::build_outcomes(&staging, epoch);
    let (quorum_met, valid_witness_count) = quorum::evaluate_quorum(&staging, epoch, &outcomes);
    let provenance_ok = provenance::all_provenance_ok(&staging.witnesses, &outcomes);
    let result = VerifyResult {
        epoch,
        quorum_met,
        valid_witness_count,
        threshold: staging.policy.quorum.threshold,
        provenance_ok,
        replay_deduped: staging.replay_deduped,
        witnesses: outcomes,
    };
    write_json(verdict_path, &result)
}

fn read_json<T: serde::de::DeserializeOwned>(path: &str) -> Result<T, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn write_json(path: &str, value: &impl serde::Serialize) -> Result<(), String> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, text + "\n").map_err(|e| e.to_string())
}
