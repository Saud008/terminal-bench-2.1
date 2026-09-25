pub mod publish;
pub mod scan;

use std::path::Path;

pub fn export_table(table: &str, out: &Path) -> Result<(), String> {
    let rows = scan::scan_committed_table(table)?;
    if let Some(parent) = out.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("mkdir export: {e}"))?;
    }
    std::fs::write(out, serde_json::to_string_pretty(&rows).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write export: {e}"))?;
    Ok(())
}
