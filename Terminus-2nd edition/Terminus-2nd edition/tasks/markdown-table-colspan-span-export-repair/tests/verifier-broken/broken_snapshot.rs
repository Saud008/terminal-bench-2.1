use serde::{Deserialize, Serialize};

use crate::model::TableExport;

pub const GRID_SNAPSHOT_PATH: &str = "/app/state/grid.snapshot.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GridSnapshot {
    pub version: u32,
    pub export: TableExport,
}

pub fn write_grid_snapshot(doc: &TableExport) -> anyhow::Result<()> {
    let _ = doc;
    Ok(())
}

pub fn read_grid_snapshot() -> anyhow::Result<TableExport> {
    anyhow::bail!("grid snapshot missing")
}
