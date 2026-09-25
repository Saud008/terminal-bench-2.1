use crate::{trial_digest, LATCH_PATH};
use serde_json::Value;
use std::{fs, path::Path};

pub fn compile_trial(trial_id: &str, root: &str) -> Result<(), String> {
    let protocol_path = Path::new(root).join("trials").join(format!("{trial_id}.json"));
    let raw = fs::read_to_string(&protocol_path).map_err(|e| e.to_string())?;
    let protocol: Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let digest = trial_digest::protocol_digest(&protocol)?;
    let latch = serde_json::json!({
        "trial_id": trial_id,
        "protocol_version": protocol["protocol_version"],
        "arms": protocol["arms"],
        "block_sizes": protocol["block_sizes"],
        "strata": protocol["strata"],
        "seed_salt": protocol["seed_salt"],
        "protocol_digest": digest,
        "log_relpath": format!("logs/{trial_id}.ndjson"),
    });
    if let Some(parent) = Path::new(LATCH_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(LATCH_PATH, serde_json::to_string_pretty(&latch).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
