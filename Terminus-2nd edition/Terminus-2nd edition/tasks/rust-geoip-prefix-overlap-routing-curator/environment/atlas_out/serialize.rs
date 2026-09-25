use crate::types::{Config, OverlapReport};
use std::fs;
use std::path::Path;

/// STUB — build sealed overlap atlas from on-disk feed-cache + ledger only.
/// Implement winner selection, asn_lineage, containment, overlap_pairs, and audit_digest
/// per /app/docs/atlas-overlap-fields.md, /app/docs/asn-conflict-lineage.md,
/// /app/docs/duplicate-prefix-precedence.md, and /app/docs/prefix-overlap-ops-contract.md.
pub fn build_report(_cfg: &Config, _seed: &str, _bundle: &str) -> Result<OverlapReport, String> {
    Err("STUB: build_report not implemented".into())
}

pub fn write_report(path: &Path, rep: &OverlapReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(rep).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
