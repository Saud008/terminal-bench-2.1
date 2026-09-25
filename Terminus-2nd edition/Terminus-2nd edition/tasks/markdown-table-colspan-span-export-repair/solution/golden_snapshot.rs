use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::model::TableExport;

pub const GRID_SNAPSHOT_PATH: &str = "/app/state/grid.snapshot.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GridSnapshot {
    pub version: u32,
    pub export: TableExport,
}

pub fn write_grid_snapshot(doc: &TableExport) -> anyhow::Result<()> {
    let snap = GridSnapshot {
        version: 1,
        export: doc.clone(),
    };
    let data = serde_json::to_string_pretty(&snap)?;
    if let Some(parent) = Path::new(GRID_SNAPSHOT_PATH).parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(GRID_SNAPSHOT_PATH, format!("{data}\n"))?;
    Ok(())
}

pub fn read_grid_snapshot() -> anyhow::Result<TableExport> {
    let raw = fs::read_to_string(GRID_SNAPSHOT_PATH)?;
    let snap: GridSnapshot = serde_json::from_str(&raw)?;
    Ok(snap.export)
}
