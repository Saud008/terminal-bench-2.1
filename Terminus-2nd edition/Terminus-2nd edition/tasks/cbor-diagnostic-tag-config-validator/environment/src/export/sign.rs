use std::fs;
use std::path::Path;

use crate::cbor::canonical;
use crate::db::audit::AuditStore;
use crate::model::types::StagingSnapshot;
use crate::sign::hmac;
use crate::staging::write;

pub fn run(out_path: &Path, ingest_path: Option<&Path>) -> Result<(), String> {
    let staged_file = write::read_staging_bytes()?;
    let snapshot = load_snapshot()?;
    let canonical_bytes = canonical::encode_staging(&snapshot);

    let sign_message = if let Some(src) = ingest_path {
        fs::read(src).map_err(|e| e.to_string())?
    } else {
        staged_file
    };

    let digest = hmac::sha256_hex(&canonical_bytes);
    let signature = hmac::hmac_sha256_hex(&sign_message)?;

    let store = AuditStore::open()?;
    let audit_row_count = store.count_for_bundle(&snapshot.bundle_id)?;

    let report = serde_json::json!({
        "bundle_id": snapshot.bundle_id,
        "staged_digest": digest,
        "signature": signature,
        "audit_row_count": audit_row_count,
        "diagnostic_tag_summary": snapshot.diagnostic_tags,
    });

    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(out_path, serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    println!("exported attestation for {}", report["bundle_id"]);
    Ok(())
}

fn load_snapshot() -> Result<StagingSnapshot, String> {
    let store = AuditStore::open()?;
    store.latest_snapshot()
}
