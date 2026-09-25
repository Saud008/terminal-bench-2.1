use std::fs;
use std::path::Path;

use anyhow::{Context, Result};

use crate::model::{ExportDoc, NhSnapshotDoc};
use crate::route_table_digest::route_table_digest;

pub fn write_export_from_nh_snapshot(export_path: &Path, nh_snapshot_path: &Path) -> Result<()> {
    let nh_body = fs::read_to_string(nh_snapshot_path)
        .with_context(|| format!("read nh snapshot {}", nh_snapshot_path.display()))?;
    let nh: NhSnapshotDoc = serde_json::from_str(&nh_body)?;
    if nh.version != 1 {
        anyhow::bail!("unsupported nh snapshot version");
    }
    let mut routes = nh.routes;
    routes.sort_by_key(|r| r.table);
    let export_digest = route_table_digest(&nh.seed, &routes);
    let doc = ExportDoc {
        pipeline_version: 1,
        seed: nh.seed,
        routes,
        export_digest,
    };
    let json = serde_json::to_string_pretty(&doc)?;
    if let Some(parent) = export_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(export_path, format!("{json}\n"))?;
    Ok(())
}
