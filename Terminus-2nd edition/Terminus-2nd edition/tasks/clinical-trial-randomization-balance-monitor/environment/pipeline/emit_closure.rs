use crate::{imbalance_ledger, BALANCE_PATH};
use serde_json::Value;
use std::{fs, path::Path};

pub fn emit_closure(trial_id: &str, _root: &str, out: &str) -> Result<(), String> {
    let balance: Value = serde_json::from_str(&fs::read_to_string(BALANCE_PATH).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if balance["trial_id"].as_str() != Some(trial_id) {
        return Err("trial mismatch".into());
    }
    let run_id = balance["run_id"].as_u64().unwrap_or(0);
    if run_id == 0 {
        return Err("run_id must be positive".into());
    }
    let max_skew = balance["max_skew"].as_u64().unwrap_or(0) as u32;
    let digest = imbalance_ledger::closure_digest(
        trial_id,
        balance["protocol_digest"].as_str().unwrap_or(""),
        max_skew,
        run_id as u32,
    );
    let closure = serde_json::json!({
        "trial_id": trial_id,
        "protocol_digest": balance["protocol_digest"],
        "run_id": run_id,
        "per_stratum": balance["per_stratum"],
        "max_skew": max_skew,
        "venues_at_cap": balance["venues_at_cap"],
        "open_slots": balance["open_slots"],
        "closure_digest": digest,
    });
    if let Some(parent) = Path::new(out).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out, serde_json::to_string_pretty(&closure).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
