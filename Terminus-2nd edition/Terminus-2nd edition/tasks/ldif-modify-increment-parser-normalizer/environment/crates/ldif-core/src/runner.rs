use std::fs;
use std::path::Path;

use crate::apply;
use crate::audit;
use crate::error::{LdifError, Result};
use crate::parser;

pub fn apply_file(
    input: &Path,
    seed: &str,
    export_path: &Path,
    audit_db: &Path,
) -> Result<()> {
    let raw = fs::read_to_string(input).map_err(|err| LdifError::Io(err.to_string()))?;
    let records = parser::parse_ldif(&raw)?;
    let (export, rows) = apply::apply_records(seed, &records)?;
    audit::write_audit(audit_db, seed, &rows)?;
    write_json(export_path, &export)?;
    Ok(())
}

pub fn query_audit(audit_db: &Path, seed: &str, export_path: &Path) -> Result<i32> {
    let doc = audit::query_audit(audit_db, seed)?;
    if doc.operations.is_empty() {
        return Ok(2);
    }
    write_json(export_path, &doc)?;
    Ok(0)
}

fn write_json(path: &Path, doc: &impl serde::Serialize) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|err| LdifError::Io(err.to_string()))?;
    }
    let json = serde_json::to_string_pretty(doc).map_err(|err| LdifError::Io(err.to_string()))?;
    fs::write(path, format!("{json}\n")).map_err(|err| LdifError::Io(err.to_string()))
}
