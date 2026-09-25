use crate::commit::state::load_committed;
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct WalkReport {
    pub table: String,
    pub root_height: u32,
    pub leaf_count: u32,
    pub key_count: u32,
    pub physical_entry_count: u32,
    pub height_recorded_before_child_fsync: bool,
}

pub fn walk_table(table: &str) -> Result<WalkReport, String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let record = crate::commit::barrier::load_commit_record()?;
    Ok(WalkReport {
        table: table.to_string(),
        root_height: tree.height,
        leaf_count: crate::btree::leaf_count(&tree),
        key_count: crate::btree::unique_key_count(&tree),
        physical_entry_count: crate::btree::physical_entry_count(&tree),
        height_recorded_before_child_fsync: record.height_recorded_before_child_fsync,
    })
}
