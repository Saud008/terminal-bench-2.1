use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

use crate::model::{BindSnapshotDoc, NexthopOut, RawRoute, RouteOut};

pub fn bind_routes(seed: &str, raw: Vec<RawRoute>) -> Vec<RouteOut> {
    raw.into_iter()
        .map(|route| bind_one(seed, &route))
        .collect()
}

fn bind_one(seed: &str, route: &RawRoute) -> RouteOut {
    let table = route.table_attr.unwrap_or(route.table_id);
    let family = if route.family == crate::attr::AF_INET {
        "inet4".to_string()
    } else {
        "inet6".to_string()
    };
    let dst = format!("{}/{}", format_addr(&route.dst, route.family), route.dst_plen);
    let mut nexthops = Vec::new();
    if !route.multipath.is_empty() {
        for (idx, hop) in route.multipath.iter().enumerate() {
            nexthops.push(NexthopOut {
                id: (idx as u32) + 1,
                ifindex: hop.ifindex,
                weight: scaled_weight(seed, hop.weight_raw),
                gateway: hop.gateway.as_ref().map(|g| format_addr(g, hop.gw_family)),
                metrics: BTreeMap::new(),
            });
        }
    } else {
        nexthops.push(NexthopOut {
            id: route.nh_id_hint.unwrap_or(0),
            ifindex: route.oif.unwrap_or(0) as i32,
            weight: 1,
            gateway: route.gateway.as_ref().map(|g| format_addr(g, route.family)),
            metrics: route.metrics.clone(),
        });
    }
    RouteOut {
        family,
        table,
        dst,
        priority: route.priority,
        nexthops,
    }
}

fn weight_scale(seed: &str) -> u32 {
    let digest = Sha256::digest(seed.as_bytes());
    (digest[0] as u32 % 32) + 1
}

fn scaled_weight(seed: &str, raw: u8) -> u32 {
    let scale = weight_scale(seed);
    ((raw as u32 * scale) % 255) + 1
}

fn format_addr(addr: &[u8], family: u8) -> String {
    if family == crate::attr::AF_INET && addr.len() >= 4 {
        format!("{}.{}.{}.{}", addr[0], addr[1], addr[2], addr[3])
    } else if addr.len() == 16 {
        format_ipv6(addr)
    } else {
        "0.0.0.0".to_string()
    }
}

fn format_ipv6(addr: &[u8]) -> String {
    addr.chunks(2)
        .map(|chunk| format!("{:x}", u16::from_be_bytes([chunk[0], chunk[1]])))
        .collect::<Vec<_>>()
        .join(":")
}

pub fn write_bind_snapshot(
    dump: &Path,
    seed: &str,
    mut routes: Vec<RouteOut>,
) -> anyhow::Result<PathBuf> {
    for route in &mut routes {
        route.nexthops.sort_by_key(|nh| nh.weight);
    }
    let name = dump
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("dump.bin");
    let snapshot = PathBuf::from(format!(
        "/app/state/bind-snapshots/{}-{}.json",
        name,
        std::process::id()
    ));
    let doc = BindSnapshotDoc {
        version: 1,
        seed: seed.to_string(),
        source_dump: dump.to_string_lossy().into_owned(),
        routes,
    };
    let json = serde_json::to_string_pretty(&doc)?;
    if let Some(parent) = snapshot.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&snapshot, format!("{json}\n"))?;
    Ok(snapshot)
}
