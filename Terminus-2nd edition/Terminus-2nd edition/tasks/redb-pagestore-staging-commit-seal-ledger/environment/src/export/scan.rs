use crate::staging::load_staging;

#[derive(serde::Serialize)]
pub struct ExportRow {
    pub key: String,
    pub value: String,
}

pub fn scan_committed_table(table: &str) -> Result<Vec<ExportRow>, String> {
    let staging = load_staging()?;
    let tree = staging
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
