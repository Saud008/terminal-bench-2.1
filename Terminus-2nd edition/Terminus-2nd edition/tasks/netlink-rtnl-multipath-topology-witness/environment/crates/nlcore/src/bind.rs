use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

use crate::model::{BindSnapshotDoc, NexthopOut, RawRoute, RouteOut};

static mut GLOBAL_NH: u32 = 0;

pub fn bind_routes(seed: &str, raw: Vec<RawRoute>) -> Vec<RouteOut> {
    let mut out = Vec::new();
    for route in raw {
        out.push(bind_one(seed, &route));
    }
    out
}

fn bind_one(seed: &str, route: &RawRoute) -> RouteOut {
    let table = match route.table_attr {
        Some(_) => route.table_id,
        None => route.table_attr.unwrap_or(route.table_id),
    };
    let family = if route.family == crate::attr::AF_INET {
        "inet4".to_string()
    } else {
        "inet6".to_string()
    };
    let dst = format_dst(&route.dst, route.dst_plen, route.family);
    let mut nexthops = Vec::new();
    if !route.multipath.is_empty() {
        for hop in &route.multipath {
            let id = next_global_id();
            nexthops.push(NexthopOut {
                id,
                ifindex: hop.ifindex,
                weight: scaled_weight(seed, hop.weight_raw),
                gateway: hop.gateway.as_ref().map(|g| format_addr(g, hop.gw_family)),
                metrics: route.metrics.clone(),
            });
        }
    } else {
        let id = route.nh_id_hint.unwrap_or(0);
        nexthops.push(NexthopOut {
            id,
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

fn scaled_weight(seed: &str, raw: u8) -> u32 {
    let scale = weight_scale(seed);
    (raw as u32).saturating_add(scale)
}

fn weight_scale(seed: &str) -> u32 {
    let digest = Sha256::digest(seed.as_bytes());
    (digest[0] as u32 % 32) + 1
}

fn next_global_id() -> u32 {
    unsafe {
        GLOBAL_NH += 1;
        GLOBAL_NH
    }
}

fn format_dst(addr: &[u8], plen: u8, family: u8) -> String {
    format!("{}/{}", format_addr(addr, family), plen)
}

fn format_addr(addr: &[u8], family: u8) -> String {
    if family == crate::attr::AF_INET && addr.len() >= 4 {
        format!(
            "{}.{}.{}.{}",
            addr[0], addr[1], addr[2], addr[3]
        )
    } else if addr.len() == 16 {
        format_ipv6(addr)
    } else {
        "0.0.0.0".to_string()
    }
}

fn format_ipv6(addr: &[u8]) -> String {
    addr.chunks(2)
        .map(|chunk| format!("{:04x}", u16::from_be_bytes([chunk[0], chunk[1]])))
        .collect::<Vec<_>>()
        .join(":")
}

pub fn write_bind_snapshot(
    dump: &Path,
    seed: &str,
    routes: Vec<RouteOut>,
) -> anyhow::Result<PathBuf> {
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
