pub mod publish;
pub mod range;
pub mod scan;

use range::ExportRow;
use std::path::Path;

pub fn export_table(table: &str, out: &Path) -> Result<(), String> {
    let rows = scan::scan_committed_table(table)?;
    write_rows(out, &rows)
}

pub fn export_range(table: &str, start: &str, end: &str, out: &Path) -> Result<(), String> {
    let rows = range::scan_range(table, start, end)?;
    write_rows(out, &rows)
}

fn write_rows(out: &Path, rows: &[ExportRow]) -> Result<(), String> {
    if let Some(parent) = out.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("mkdir export: {e}"))?;
    }
    std::fs::write(out, serde_json::to_string_pretty(rows).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write export: {e}"))?;
    Ok(())
}
