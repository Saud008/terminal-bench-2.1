use std::fs;
use std::path::Path;

use crate::cbor::canonical;
use crate::model::types::StagingSnapshot;

pub const STAGING_PATH: &str = "/app/state/staging.cbor";

pub fn write_staging(snapshot: &StagingSnapshot) -> Result<Vec<u8>, String> {
    if let Some(parent) = Path::new(STAGING_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let bytes = canonical::encode_staging(snapshot);
    fs::write(STAGING_PATH, &bytes).map_err(|e| e.to_string())?;
    validate_staging(snapshot)?;
    Ok(bytes)
}

pub fn read_staging_bytes() -> Result<Vec<u8>, String> {
    fs::read(STAGING_PATH).map_err(|e| e.to_string())
}

fn validate_staging(snapshot: &StagingSnapshot) -> Result<(), String> {
    if snapshot.bundle_id.is_empty() {
        return Err("empty bundle_id".into());
    }
    if snapshot.envelope.policy.is_empty() {
        return Err("empty policy".into());
    }
    if snapshot.envelope.nonce.is_empty() {
        return Err("empty nonce".into());
    }
    Ok(())
}
