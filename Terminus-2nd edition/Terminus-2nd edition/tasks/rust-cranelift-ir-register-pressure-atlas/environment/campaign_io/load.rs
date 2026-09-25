use crate::fluence_models::BundleFile;
use std::fs;
use std::path::Path;

pub fn load_bundle(path: &Path) -> Result<BundleFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("bundle read {}: {e}", path.display()))?;
    serde_json::from_str(&raw).map_err(|e| format!("bundle parse: {e}"))
}
