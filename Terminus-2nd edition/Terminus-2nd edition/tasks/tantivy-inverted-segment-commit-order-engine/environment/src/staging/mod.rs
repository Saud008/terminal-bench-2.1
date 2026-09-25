use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

const CATALOG_PATH: &str = "/app/state/index-catalog.json";
const SNAPSHOT_PATH: &str = "/app/state/index-snapshot.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct IndexState {
    pub staging_segment_ids: Vec<String>,
    pub committed_segment_ids: Vec<String>,
    pub obsolete_segment_ids: Vec<String>,
    pub reader_registry: Vec<String>,
    pub pending_live_docs: u32,
    pub committed_live_docs: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct IndexCatalog {
    pub indexes: HashMap<String, IndexState>,
}

pub fn load_catalog() -> Result<IndexCatalog, String> {
    if !Path::new(CATALOG_PATH).exists() {
        return Ok(IndexCatalog::default());
    }
    let raw = fs::read_to_string(CATALOG_PATH).map_err(|e| format!("read catalog: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse catalog: {e}"))
}

pub fn save_catalog(cat: &IndexCatalog) -> Result<(), String> {
    if let Some(parent) = Path::new(CATALOG_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir catalog: {e}"))?;
    }
    fs::write(
        CATALOG_PATH,
        serde_json::to_string_pretty(cat).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("write catalog: {e}"))?;
    Ok(())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexSnapshot {
    pub index: String,
    pub live_doc_count: u32,
    pub segment_count: u32,
    pub posting_checksum: u64,
    pub dangling_reader_count: u32,
}

pub fn write_snapshot(
    index: &str,
    live_docs: u32,
    segment_count: u32,
    posting_checksum: u64,
    dangling: u32,
) -> Result<(), String> {
    let snap = IndexSnapshot {
        index: index.to_string(),
        live_doc_count: live_docs,
        segment_count,
        posting_checksum,
        dangling_reader_count: dangling,
    };
    if let Some(parent) = Path::new(SNAPSHOT_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir snapshot: {e}"))?;
    }
    fs::write(
        SNAPSHOT_PATH,
        serde_json::to_string_pretty(&snap).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("write snapshot: {e}"))?;
    Ok(())
}

pub fn dangling_readers(state: &IndexState) -> u32 {
    let obsolete: std::collections::HashSet<&str> = state
        .obsolete_segment_ids
        .iter()
        .map(String::as_str)
        .collect();
    state
        .reader_registry
        .iter()
        .filter(|id| obsolete.contains(id.as_str()))
        .count() as u32
}
