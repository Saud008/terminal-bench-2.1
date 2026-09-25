use crate::{beta_norm, LATCH_PATH, CHRONICLE_PATH};
use serde_json::Value;
use std::{fs, path::Path};

pub fn accept_log(trial_id: &str, root: &str) -> Result<(), String> {
    let latch: Value = serde_json::from_str(&fs::read_to_string(LATCH_PATH).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if latch["trial_id"].as_str() != Some(trial_id) {
        return Err("trial mismatch".into());
    }
    let log_path = Path::new(root).join(latch["log_relpath"].as_str().unwrap_or(""));
    let mut rows: Vec<Value> = Vec::new();
    for line in fs::read_to_string(&log_path).map_err(|e| e.to_string())?.lines() {
        if line.trim().is_empty() {
            continue;
        }
        rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let raw_count = rows.len();
    beta_norm::normalize_rows(&mut rows);
    let chronicle = serde_json::json!({
        "trial_id": trial_id,
        "protocol_digest": latch["protocol_digest"],
        "raw_count": raw_count,
        "normalized_count": rows.len(),
        "rows": rows,
    });
    if let Some(parent) = Path::new(CHRONICLE_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(CHRONICLE_PATH, serde_json::to_string_pretty(&chronicle).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
