use std::fs;
use std::path::Path;

use crate::model::TableExport;

pub fn write_json(path: &Path, doc: &TableExport) -> anyhow::Result<()> {
    let data = serde_json::to_string_pretty(doc)?;
    fs::write(path, format!("{data}\n"))?;
    Ok(())
}
