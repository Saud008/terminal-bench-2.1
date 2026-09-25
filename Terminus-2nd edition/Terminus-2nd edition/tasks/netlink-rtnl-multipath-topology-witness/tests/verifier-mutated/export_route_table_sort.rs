use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use sha2::{Digest, Sha256};

use crate::model::{ExportDoc, NhSnapshotDoc};

pub fn write_export_from_nh_snapshot(export_path: &Path, nh_snapshot_path: &Path) -> Result<()> {
    let body = fs::read_to_string(nh_snapshot_path)
        .with_context(|| format!("read nh snapshot {}", nh_snapshot_path.display()))?;
    let nh: NhSnapshotDoc = serde_json::from_str(&body)?;
    if nh.version != 1 {
        anyhow::bail!("unsupported nh snapshot version");
    }
    let mut routes = nh.routes;
    routes.sort_by_key(|r| r.table);
    let export_digest = format!(
        "{:x}",
        Sha256::digest(format!("{}{}", nh.seed, routes.len()).as_bytes())
    );
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
