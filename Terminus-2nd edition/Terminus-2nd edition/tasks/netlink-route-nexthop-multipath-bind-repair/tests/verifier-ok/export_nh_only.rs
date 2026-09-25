use std::fs;
use std::path::Path;

use anyhow::{Context, Result};

use crate::model::{BindSnapshotDoc, ExportDoc};

pub fn write_export_from_snapshot(export_path: &Path, snapshot_path: &Path) -> Result<()> {
    let body = fs::read_to_string(snapshot_path)
        .with_context(|| format!("read snapshot {}", snapshot_path.display()))?;
    let snap: BindSnapshotDoc = serde_json::from_str(&body)?;
    let mut routes = snap.routes;
    for route in &mut routes {
        route.nexthops.sort_by_key(|nh| nh.id);
    }
    routes.sort_by_key(|r| r.table);
    let doc = ExportDoc {
        pipeline_version: 1,
        seed: snap.seed,
        routes,
    };
    let json = serde_json::to_string_pretty(&doc)?;
    if let Some(parent) = export_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(export_path, format!("{json}\n"))?;
    Ok(())
}
