use std::fs;
use std::path::Path;

use crate::model::{MigrateExport, MigrateSnapshot};

pub const DEFAULT_PATH: &str = "/app/state/archectl-migrate-snapshot.json";

pub fn write(path: &str, doc: &MigrateExport) -> std::io::Result<()> {
    let snap = MigrateSnapshot::from(doc.clone());
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent)?;
    }
    let raw = serde_json::to_string_pretty(&snap)?;
    fs::write(path, format!("{raw}\n"))
}

pub fn load(path: &str) -> Result<MigrateSnapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
