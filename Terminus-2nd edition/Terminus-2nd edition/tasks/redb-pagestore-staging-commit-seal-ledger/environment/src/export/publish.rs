use crate::commit::state::CommittedState;

#[derive(serde::Serialize)]
pub struct ExportRow {
    pub key: String,
    pub value: String,
}

pub fn publish_committed_table(table: &str, committed: &CommittedState) -> Result<Vec<ExportRow>, String> {
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
