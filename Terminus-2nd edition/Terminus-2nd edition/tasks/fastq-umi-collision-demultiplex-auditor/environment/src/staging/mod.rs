use std::fs;
use std::path::Path;

use crate::types::StagingFile;

pub fn load_staging(path: &str) -> Result<StagingFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_staging(path: &str, staging: &StagingFile) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(staging).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn load_ledger(path: &str) -> Result<crate::types::LedgerFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_ledger(path: &str, ledger: &crate::types::LedgerFile) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(ledger).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn lane_by_id<'a>(staging: &'a StagingFile, lane_id: &str) -> Option<&'a crate::types::LaneConfig> {
    staging.lanes.iter().find(|l| l.lane_id == lane_id)
}
