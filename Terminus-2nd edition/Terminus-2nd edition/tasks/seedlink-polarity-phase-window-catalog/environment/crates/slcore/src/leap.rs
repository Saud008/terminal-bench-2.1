use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use serde::Deserialize;

use crate::error::SlError;

pub fn leap_config_root() -> PathBuf {
    if let Ok(root) = std::env::var("TB3_LEAP_ROOT") {
        if !root.is_empty() {
            return PathBuf::from(root);
        }
    }
    PathBuf::from("/app/config/leap")
}

pub fn load_leap_epochs(root: Option<&Path>) -> Result<HashSet<u32>, SlError> {
    let base = root.map(Path::to_path_buf).unwrap_or_else(leap_config_root);
    let path = base.join("leap-epochs.json");
    if !path.is_file() {
        return Ok(HashSet::new());
    }
    let text = fs::read_to_string(path)?;
    let data: LeapFile = serde_json::from_str(&text)?;
    Ok(data.positive_leap_epochs.into_iter().collect())
}

#[derive(Debug, Deserialize)]
struct LeapFile {
    positive_leap_epochs: Vec<u32>,
}

pub fn leap_adjust_us(_epoch_sec: u32, _leap_marker: u8, _leap_epochs: &HashSet<u32>) -> u64 {
    0
}
