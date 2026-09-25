pub mod reclaim;

use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};

use crate::merge;
use crate::staging;
use crate::types::{CompactState, GovernorReport};
use crate::witness;

pub fn compact_export(
    stage_path: &str,
    governor_path: &str,
    checksum_path: &str,
    state_path: &str,
    pass: u32,
) -> Result<(), String> {
    let stage = staging::load_stage(stage_path)?;
    if stage.wal_batches.is_empty() && stage.sst_files.is_empty() {
        return Err("empty staging".into());
    }

    let mut report = merge::build_governor_report(&stage, pass);
    let fresh_reclaimed = report.reclaimed_bytes;

    if witness::idempotency::should_reuse_state(pass) {
        if let Ok(prev) = load_compact_state(state_path) {
            report.reclaimed_bytes =
                witness::idempotency::merge_reclaimed(&prev, fresh_reclaimed);
        }
    }

    write_governor(&report, governor_path)?;
    let digest = checksum_from_report(&report)?;
    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    fs::write(checksum_path, format!("{digest}\n")).map_err(|e| e.to_string())?;

    save_compact_state(
        state_path,
        &CompactState {
            reclaimed_bytes: report.reclaimed_bytes,
            compact_pass: pass,
        },
    )
}

fn write_governor(report: &GovernorReport, path: &str) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, format!("{pretty}\n")).map_err(|e| e.to_string())
}

pub fn checksum_from_report(report: &GovernorReport) -> Result<String, String> {
    let mut canonical = report.clone();
    canonical.compact_pass = 0;
    let bytes = serde_json::to_vec(&canonical).map_err(|e| e.to_string())?;
    let hash = Sha256::digest(bytes);
    Ok(hex::encode(hash))
}

fn load_compact_state(path: &str) -> Result<CompactState, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn save_compact_state(path: &str, state: &CompactState) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(state).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
