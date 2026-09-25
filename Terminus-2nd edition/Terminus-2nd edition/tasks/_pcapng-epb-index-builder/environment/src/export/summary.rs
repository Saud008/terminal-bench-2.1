use std::collections::HashMap;
use std::fs;

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::db::Store;
use crate::index::INDEX_PATH;

#[derive(Serialize)]
struct IfaceView {
    interface_id: u32,
    if_name: String,
    packet_count: usize,
}

#[derive(Serialize)]
struct SummaryReport {
    packet_count: usize,
    interfaces: Vec<IfaceView>,
    index_digest: String,
    crc_rejected: i64,
    duplicate_rejected: i64,
}

pub fn write_summary(store: &Store, out_path: &str) -> Result<(), String> {
    let packets = store.all_packets().map_err(|e| e.to_string())?;
    let meta = store.iface_meta().map_err(|e| e.to_string())?;
    let (crc_rejected, duplicate_rejected, _accepted) =
        store.ingest_stats().map_err(|e| e.to_string())?;

    let mut per_iface: HashMap<u32, usize> = HashMap::new();
    for pkt in &packets {
        *per_iface.entry(pkt.interface_id).or_insert(0) += 1;
    }

    let mut interfaces = Vec::new();
    for (iface_id, name) in meta {
        interfaces.push(IfaceView {
            interface_id: iface_id,
            if_name: name,
            packet_count: per_iface.get(&iface_id).copied().unwrap_or(0),
        });
    }
    interfaces.sort_by_key(|i| i.interface_id);

    let packet_count: usize = interfaces.iter().map(|i| i.packet_count).sum();

    let index_digest = index_digest()?;
    let report = SummaryReport {
        packet_count,
        interfaces,
        index_digest,
        crc_rejected,
        duplicate_rejected,
    };

    let body = serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(out_path, body).map_err(|e| e.to_string())
}

fn index_digest() -> Result<String, String> {
    let bytes = fs::read(INDEX_PATH).map_err(|e| e.to_string())?;
    Ok(format!("{:x}", Sha256::digest(&bytes)))
}
