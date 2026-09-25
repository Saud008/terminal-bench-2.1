use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use sha2::{Digest, Sha256};

use crate::model::{ExportDoc, NhSnapshotDoc, RouteOut};

fn route_row_lines(routes: &[RouteOut]) -> Vec<String> {
    let mut parts = Vec::new();
    for route in routes {
        parts.push(route.family.clone());
        parts.push(route.table.to_string());
        parts.push(route.dst.clone());
        match route.priority {
            Some(p) => parts.push(p.to_string()),
            None => parts.push("-".to_string()),
        }
        for nh in &route.nexthops {
            parts.push(nh.id.to_string());
            parts.push(nh.ifindex.to_string());
            parts.push(nh.weight.to_string());
            if let Some(gw) = &nh.gateway {
                parts.push(gw.clone());
            } else {
                parts.push("-".to_string());
            }
            for (k, v) in &nh.metrics {
                parts.push(format!("{k}:{v}"));
            }
        }
    }
    parts
}

fn snapshot_fingerprint(routes: &[RouteOut]) -> String {
    let joined = route_row_lines(routes).join("\n");
    format!("{:x}", Sha256::digest(joined.as_bytes()))
}

fn compute_export_digest(
    seed: &str,
    source_dump: &str,
    snapshot_routes: &[RouteOut],
    export_routes: &[RouteOut],
) -> String {
    let mut parts = vec![
        "1".to_string(),
        seed.to_string(),
        source_dump.to_string(),
        snapshot_fingerprint(snapshot_routes),
        export_routes.len().to_string(),
    ];
    parts.extend(route_row_lines(export_routes));
    let joined = parts.join("\n");
    format!("{:x}", Sha256::digest(joined.as_bytes()))
}

pub fn write_export_from_nh_snapshot(export_path: &Path, nh_snapshot_path: &Path) -> Result<()> {
    let body = fs::read_to_string(nh_snapshot_path)
        .with_context(|| format!("read nh snapshot {}", nh_snapshot_path.display()))?;
    let nh: NhSnapshotDoc = serde_json::from_str(&body)?;
    if nh.version != 1 {
        anyhow::bail!("unsupported nh snapshot version");
    }
    let _correct =
        compute_export_digest(&nh.seed, &nh.source_dump, &nh.snapshot_routes, &nh.routes);
    let export_digest = format!("{:x}", Sha256::digest(nh.seed.as_bytes()));
    let doc = ExportDoc {
        pipeline_version: 1,
        seed: nh.seed,
        routes: nh.routes,
        export_digest,
    };
    let json = serde_json::to_string_pretty(&doc)?;
    if let Some(parent) = export_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(export_path, format!("{json}\n"))?;
    Ok(())
}
