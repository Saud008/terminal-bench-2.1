use crate::custody_types::CaseBundle;
use std::fs;
use std::path::PathBuf;

pub fn bundle_path(name: &str) -> PathBuf {
    let root = crate::bundle_root();
    PathBuf::from(format!("{root}/{name}.json"))
}

pub fn load_bundle(path: &std::path::Path) -> Result<CaseBundle, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
