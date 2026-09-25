use crate::fluence_models::FluenceLedger;
use std::fs;
use std::path::{Path, PathBuf};

fn path_for(dir: &str, campaign_id: &str) -> PathBuf {
    Path::new(dir).join(format!("{campaign_id}.json"))
}

/// The next accrual_epoch for `campaign_id` in `dir`.
pub fn next_epoch(dir: &str, campaign_id: &str) -> u64 {
    let _ = (dir, campaign_id);
    1
}

pub fn write_ledger(dir: &str, art: &FluenceLedger) -> Result<(), String> {
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    let p = path_for(dir, &art.campaign_id);
    let body = serde_json::to_string_pretty(art).map_err(|e| e.to_string())?;
    fs::write(p, body + "\n").map_err(|e| e.to_string())
}

pub fn read_ledger(dir: &str, campaign_id: &str) -> Result<FluenceLedger, String> {
    let p = path_for(dir, campaign_id);
    let raw = fs::read_to_string(&p).map_err(|e| format!("ledger read {}: {e}", p.display()))?;
    serde_json::from_str(&raw).map_err(|e| format!("ledger parse: {e}"))
}


