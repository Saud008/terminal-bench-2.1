use crate::bundle_root;
use crate::types::BundleFile;
use std::fs;
use std::path::{Path, PathBuf};

pub fn bundle_path(name: &str) -> PathBuf {
    let root = bundle_root();
    Path::new(&root).join(format!("{name}.json"))
}

pub fn load_bundle(path: &Path) -> Result<BundleFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
