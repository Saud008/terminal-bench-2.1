use crate::btree::TableMap;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

const STAGING_PATH: &str = "/app/state/staging.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingState {
    pub tables: TableMap,
}

impl Default for StagingState {
    fn default() -> Self {
        StagingState {
            tables: TableMap::default(),
        }
    }
}

pub fn load_staging() -> Result<StagingState, String> {
    if !Path::new(STAGING_PATH).exists() {
        return Ok(StagingState::default());
    }
    let raw = fs::read_to_string(STAGING_PATH).map_err(|e| format!("read staging: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse staging: {e}"))
}

pub fn save_staging(state: &StagingState) -> Result<(), String> {
    if let Some(parent) = Path::new(STAGING_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir staging: {e}"))?;
    }
    fs::write(STAGING_PATH, serde_json::to_string_pretty(state).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write staging: {e}"))?;
    Ok(())
}

pub fn delete_key(table: &str, key: &str) -> Result<(), String> {
    let mut state = load_staging()?;
    let tree = state.tables.get_or_insert(table);
    crate::btree::delete(tree, key)?;
    save_staging(&state)
}

pub fn apply_puts(table: &str, puts: &[(String, String)]) -> Result<(), String> {
    let mut state = load_staging()?;
    let tree = state.tables.get_or_insert(table);
    for (key, value) in puts {
        crate::ingest::replay::append_put(tree, key.clone(), value.clone())?;
    }
    save_staging(&state)
}

pub fn snapshot_path() -> PathBuf {
    PathBuf::from("/app/state/sled-staging-snapshot.json")
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BTreeSnapshot {
    pub table: String,
    pub root_height: u32,
    pub leaf_count: u32,
    pub key_count: u32,
}

pub fn write_snapshot(table: &str, height: u32, leaf_count: u32, key_count: u32) -> Result<(), String> {
    let snap = BTreeSnapshot {
        table: table.to_string(),
        root_height: height,
        leaf_count,
        key_count,
    };
    let path = snapshot_path();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir snapshot: {e}"))?;
    }
    fs::write(path, serde_json::to_string_pretty(&snap).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write snapshot: {e}"))?;
    Ok(())
}
