use std::fs;
use std::path::{Path, PathBuf};

use crate::model::{BindSnapshotDoc, NexthopOut, NhSnapshotDoc};

/// Stage 2a: normalize nexthops on each bound route before export doc assembly.
pub fn normalize_route_nexthops(nexthops: &mut [NexthopOut]) {
    nexthops.sort_by_key(|nh| nh.weight);
}

pub fn write_nh_snapshot(bind_snapshot_path: &Path) -> anyhow::Result<PathBuf> {
    let body = fs::read_to_string(bind_snapshot_path)?;
    let bind: BindSnapshotDoc = serde_json::from_str(&body)?;
    let mut snapshot_routes = bind.routes.clone();
    for route in &mut snapshot_routes {
        route.nexthops.sort_by_key(|nh| nh.weight);
    }
    let mut routes = bind.routes;
    for route in &mut routes {
        normalize_route_nexthops(&mut route.nexthops);
    }
    let dump_name = Path::new(&bind.source_dump)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("dump.bin");
    let nh_path = PathBuf::from(format!(
        "/app/state/nh-snapshots/{}-{}.json",
        dump_name,
        std::process::id()
    ));
    let doc = NhSnapshotDoc {
        version: 1,
        seed: bind.seed,
        source_dump: bind.source_dump,
        bind_snapshot: bind_snapshot_path.to_string_lossy().into_owned(),
        snapshot_routes,
        routes,
    };
    let json = serde_json::to_string_pretty(&doc)?;
    if let Some(parent) = nh_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&nh_path, format!("{json}\n"))?;
    Ok(nh_path)
}
