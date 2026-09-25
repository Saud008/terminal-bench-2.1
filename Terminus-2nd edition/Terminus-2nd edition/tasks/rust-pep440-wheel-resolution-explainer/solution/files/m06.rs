use crate::m04::IndexRow;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotDoc {
    pub run_id: String,
    pub scenario: String,
    pub target_python: String,
    pub target_platform: String,
    pub target_arch: String,
    pub index_fingerprint: String,
    pub packages: Vec<IndexRow>,
    pub queries: Vec<QueryRow>,
    pub snapshot_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryRow {
    pub package: String,
    pub spec: String,
}

pub fn snapshot_digest(
    run_id: &str,
    fp: &str,
    python: &str,
    platform: &str,
    arch: &str,
    packages: &[IndexRow],
) -> String {
    let body = serde_json::json!({
        "index_fingerprint": fp,
        "packages": packages.iter().map(|p| serde_json::json!({"package": p.package, "version": p.version})).collect::<Vec<_>>(),
        "run_id": run_id,
        "target_arch": arch,
        "target_platform": platform,
        "target_python": python,
    });
    let raw = serde_json::to_string(&body).unwrap_or_default();
    hex::encode(Sha256::digest(raw.as_bytes()))
}

pub fn write_snapshot(path: &Path, doc: &SnapshotDoc) -> Result<(), String> {
    let json = serde_json::to_string_pretty(doc).map_err(|e| e.to_string())?;
    fs::write(path, format!("{json}
")).map_err(|e| e.to_string())
}

mod hex {
    pub fn encode(bytes: impl AsRef<[u8]>) -> String {
        bytes.as_ref().iter().map(|b| format!("{b:02x}")).collect()
    }
}
