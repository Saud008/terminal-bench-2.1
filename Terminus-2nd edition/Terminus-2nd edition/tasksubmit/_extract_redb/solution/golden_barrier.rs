use crate::btree::node::BTree;
use crate::storage::page_store::{flush_children, write_commit_record};
use serde::{Deserialize, Serialize};
use std::path::Path;

const RECORD_PATH: &str = "/app/state/commit_record.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CommitRecord {
    pub table: String,
    pub root_height: u32,
    pub children_fsynced: bool,
    pub height_recorded_before_child_fsync: bool,
}

pub fn load_commit_record() -> Result<CommitRecord, String> {
    if !Path::new(RECORD_PATH).exists() {
        return Ok(CommitRecord::default());
    }
    let raw = std::fs::read_to_string(RECORD_PATH).map_err(|e| format!("read record: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse record: {e}"))
}

pub fn run_commit_barrier(table: &str, height: u32, tree: &BTree) -> Result<(), String> {
    flush_children(tree)?;
    write_commit_record(table, height, true, false)?;
    Ok(())
}
