use crate::plant_schema::ShiftBundle;
use std::path::PathBuf;

pub fn bundle_path(name: &str) -> PathBuf {
    PathBuf::from(format!("{}/{}.json", crate::shift_root(), name))
}

pub fn load_bundle(path: &PathBuf) -> Result<ShiftBundle, String> {
    let raw = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
