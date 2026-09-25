// PPI scan ingest path for tilt bundle manifests.
use crate::models::ScanBundle;
use std::fs;
use std::path::Path;

pub fn read_scan_bundle(path: &Path) -> Result<ScanBundle, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
