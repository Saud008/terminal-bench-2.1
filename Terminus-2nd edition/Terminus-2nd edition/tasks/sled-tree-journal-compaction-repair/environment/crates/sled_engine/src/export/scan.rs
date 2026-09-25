use crate::commit::state::load_committed;

pub use super::range::ExportRow;

pub fn scan_committed_table(table: &str) -> Result<Vec<ExportRow>, String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let entries = crate::btree::ordered_entries(&tree);
    Ok(entries
        .into_iter()
        .map(|(key, value)| ExportRow { key, value })
        .collect())
}
