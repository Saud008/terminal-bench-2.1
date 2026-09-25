use crate::btree::{leaf_count, TableMap};
use crate::commit::barrier::run_commit_barrier;
use crate::journal::split_log::record_splits_for_table;
use crate::page::registry::sync_registry_from_tree;
use crate::staging::{load_staging, save_staging, write_snapshot};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

const COMMITTED_PATH: &str = "/app/state/committed.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CommittedState {
    pub tables: TableMap,
}

pub fn load_committed() -> Result<CommittedState, String> {
    if !Path::new(COMMITTED_PATH).exists() {
        return Ok(CommittedState::default());
    }
    let raw = fs::read_to_string(COMMITTED_PATH).map_err(|e| format!("read committed: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse committed: {e}"))
}

pub fn save_committed(state: &CommittedState) -> Result<(), String> {
    if let Some(parent) = Path::new(COMMITTED_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir committed: {e}"))?;
    }
    fs::write(COMMITTED_PATH, serde_json::to_string_pretty(state).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write committed: {e}"))?;
    Ok(())
}

pub fn commit_table(table: &str) -> Result<(), String> {
    let staging = load_staging()?;
    if !staging.tables.tables.contains_key(table) {
        return Ok(());
    }
    let tree = staging
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let height = tree.height;
    let leaves = leaf_count(&tree);
    let keys = crate::btree::unique_key_count(&tree);

    run_commit_barrier(table, height, &tree)?;

    let split_events = leaves.saturating_sub(1);
    if split_events > 0 {
        record_splits_for_table(table, split_events)?;
    }
    sync_registry_from_tree(&tree)?;

    let mut committed = load_committed()?;
    committed.tables.tables.insert(table.to_string(), tree);
    save_committed(&committed)?;

    write_snapshot(table, height, leaves, keys)?;

    let mut cleared = load_staging()?;
    cleared.tables.tables.remove(table);
    save_staging(&cleared)
}
