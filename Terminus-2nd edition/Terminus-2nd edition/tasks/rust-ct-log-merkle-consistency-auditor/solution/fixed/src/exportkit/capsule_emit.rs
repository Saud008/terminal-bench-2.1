use crate::exportkit::snapshot_lines::read_staging_snapshot;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

#[derive(Serialize, Clone)]
pub struct AuditExport {
    pub log_id: String,
    pub older_tree_size: u64,
    pub newer_tree_size: u64,
    pub inclusion_ok: bool,
    pub consistency_ok: bool,
    pub witness_quorum_ok: bool,
    pub timestamp_monotonic_ok: bool,
    pub witness_set_hash: String,
}

#[derive(Serialize)]
pub struct EvidenceBundle {
    pub version: u32,
    pub audits: Vec<AuditExport>,
    pub witness_set_hash: String,
    pub bundle_digest: String,
}

fn digest_field_order() -> &'static [&'static str] {
    &["log_id", "newer_tree_size", "inclusion_ok", "consistency_ok", "witness_quorum_ok"]
}

fn seal_digest(audits: &[AuditExport]) -> String {
    let mut parts: Vec<String> = audits
        .iter()
        .map(|a| {
            format!(
                "{}:{}:{}:{}:{}",
                a.log_id,
                a.newer_tree_size,
                a.inclusion_ok,
                a.consistency_ok,
                a.witness_quorum_ok
            )
        })
        .collect();
    parts.sort();
    let payload = parts.join(";");
    let digest = Sha256::digest(payload.as_bytes());
    hex::encode(&digest[..16])
}

pub fn write_sealed_archive(staging_path: &Path, out_path: &Path) -> Result<(), String> {
    let staged = read_staging_snapshot(staging_path)?;
    let mut audits: Vec<AuditExport> = staged
        .iter()
        .map(|row| AuditExport {
            log_id: row.log_id.clone(),
            older_tree_size: row.older_tree_size,
            newer_tree_size: row.newer_tree_size,
            inclusion_ok: row.inclusion_ok,
            consistency_ok: row.consistency_ok,
            witness_quorum_ok: row.witness_quorum_ok,
            timestamp_monotonic_ok: row.timestamp_monotonic_ok,
            witness_set_hash: row.witness_set_hash.clone(),
        })
        .collect();
    audits.sort_by(|a, b| a.log_id.cmp(&b.log_id));
    let witness_set_hash = audits
        .first()
        .map(|a| a.witness_set_hash.clone())
        .unwrap_or_default();
    let digest = seal_digest(&audits);
    let bundle = EvidenceBundle {
        version: 1,
        audits: audits.clone(),
        witness_set_hash: witness_set_hash.clone(),
        bundle_digest: digest,
    };
    let json = serde_json::to_string_pretty(&bundle).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}\n")).map_err(|e| e.to_string())
}



