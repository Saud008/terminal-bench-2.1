use crate::bundle_root;
use crate::attest_model::BundleFile;
use std::fs;
use std::path::PathBuf;

pub fn bundle_path(name: &str) -> PathBuf {
    PathBuf::from(bundle_root()).join(format!("{name}.json"))
}

pub fn load_bundle(path: &PathBuf) -> Result<BundleFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
