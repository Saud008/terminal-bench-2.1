use std::fs;
use std::path::Path;

use crate::model::{BindSnapshotDoc, RouteOut};

/// Stage 1b: validate bind snapshot invariants before NH normalization.
pub fn validate_bind_routes(routes: &[RouteOut]) -> anyhow::Result<()> {
    for route in routes {
        if route.nexthops.len() > 1 {
            for nh in &route.nexthops {
                if !nh.metrics.is_empty() {
                    anyhow::bail!("multipath nexthops must not carry route metrics");
                }
            }
        }
    }
    Ok(())
}

pub fn validate_bind_snapshot(doc: &BindSnapshotDoc) -> anyhow::Result<()> {
    if doc.version != 1 {
        anyhow::bail!("bind snapshot version mismatch");
    }
    validate_bind_routes(&doc.routes)
}

pub fn validate_bind_snapshot_file(path: &Path) -> anyhow::Result<()> {
    let body = fs::read_to_string(path)?;
    let doc: BindSnapshotDoc = serde_json::from_str(&body)?;
    validate_bind_snapshot(&doc)
}
