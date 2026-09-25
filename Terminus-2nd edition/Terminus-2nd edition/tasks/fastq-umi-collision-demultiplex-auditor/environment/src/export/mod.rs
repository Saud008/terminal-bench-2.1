pub mod contamination;

use std::fs;

use sha2::{Digest, Sha256};

use crate::staging;
use crate::types::AtlasFile;

pub fn atlas_export(
    staging_path: &str,
    ledger_path: &str,
    atlas_path: &str,
    digest_path: &str,
) -> Result<(), String> {
    let staging = staging::load_staging(staging_path)?;
    let ledger = staging::load_ledger(ledger_path)?;

    let flags = contamination::detect_contamination(&ledger.entries);

    let atlas = AtlasFile {
        atlas_version: 1,
        ingest_seq: staging.ingest_seq,
        demux_seq: ledger.demux_seq,
        clusters: ledger.clusters.clone(),
        contamination_flags: flags,
    };

    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&atlas).map_err(|e| e.to_string())?;
    fs::write(atlas_path, format!("{pretty}\n")).map_err(|e| e.to_string())?;

    let digest = checksum_from_atlas(&atlas)?;
    fs::write(digest_path, format!("{digest}\n")).map_err(|e| e.to_string())
}

pub fn checksum_from_atlas(atlas: &AtlasFile) -> Result<String, String> {
    let bytes = serde_json::to_vec(atlas).map_err(|e| e.to_string())?;
    let hash = Sha256::digest(bytes);
    Ok(hex::encode(hash))
}
