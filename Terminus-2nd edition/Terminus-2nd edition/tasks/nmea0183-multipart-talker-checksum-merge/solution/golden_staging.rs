use std::fs;
use std::path::Path;

use crate::export::{validate, wrap, writer};
use crate::model::{MergeReport, MergeSnapshot};

pub fn write_snapshot(path: &Path, snapshot: &MergeSnapshot) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(snapshot).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| e.to_string())
}

pub fn read_snapshot(path: &Path) -> Result<MergeSnapshot, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

pub fn publish_export(snapshot_path: &Path, output_path: &Path) -> Result<MergeReport, String> {
    let snapshot = read_snapshot(snapshot_path)?;
    writer::verify_digest(&snapshot)?;
    validate::validate_snapshot(&snapshot)?;
    let report = wrap::build_report(&snapshot);
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(output_path, text).map_err(|e| e.to_string())?;
    Ok(report)
}
