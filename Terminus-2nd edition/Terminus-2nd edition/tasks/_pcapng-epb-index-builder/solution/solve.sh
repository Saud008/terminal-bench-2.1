#!/bin/bash
set -euo pipefail

cd /app

python3 <<'PY'
from pathlib import Path

root = Path("/app/src")

# Bug 1: advance using block_total_length
block = root / "parse/block.rs"
block.write_text(
    """/// Block traversal helpers.

pub fn body_len(block_total_length: u32) -> usize {
    if block_total_length < 12 {
        return 0;
    }
    block_total_length as usize - 12
}

/// Advance offset after consuming a block.
pub fn next_block_offset(current: usize, block_total_length: u32, _body_len: usize) -> usize {
    current + block_total_length as usize
}
"""
)

# Bug 2: zero-based interface ids
iface = root / "parse/interface.rs"
iface.write_text(
    """use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct InterfaceInfo {
    pub id: u32,
    pub name: String,
}

pub struct InterfaceMap {
    next_id: u32,
    by_file_id: HashMap<u32, InterfaceInfo>,
    ordered: Vec<InterfaceInfo>,
}

impl InterfaceMap {
    pub fn new() -> Self {
        Self {
            next_id: 0,
            by_file_id: HashMap::new(),
            ordered: Vec::new(),
        }
    }

    pub fn register(&mut self, file_iface_id: u32, name: String) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        let info = InterfaceInfo {
            id,
            name: name.clone(),
        };
        self.by_file_id.insert(file_iface_id, info.clone());
        self.ordered.push(info);
        id
    }

    pub fn resolve(&self, raw_iface: u32) -> Option<u32> {
        self.by_file_id.get(&raw_iface).map(|i| i.id)
    }

    pub fn all(&self) -> &[InterfaceInfo] {
        &self.ordered
    }
}
"""
)

# Bug 3: validate CRC before indexing
staging = root / "ingest/staging.rs"
text = staging.read_text()
text = text.replace(
    """    let key = replay_key(iface, epb.ts_ns, file_offset);
    let _ = store.insert_packet(
        iface,
        epb.ts_ns,
        file_offset,
        epb.cap_len,
        epb.packet_len,
        &key,
    );

    if let Some(expected) = epb.crc_expected {
        if !epb_core_crc_ok(&core, expected) {
            store.record_crc_reject().map_err(|e| e.to_string())?;
        }
    }""",
    """    if let Some(expected) = epb.crc_expected {
        if !epb_core_crc_ok(&core, expected) {
            store.record_crc_reject().map_err(|e| e.to_string())?;
            return Ok(());
        }
    }

    let key = replay_key(iface, epb.ts_ns, file_offset);
    let _ = store.insert_packet(
        iface,
        epb.ts_ns,
        file_offset,
        epb.cap_len,
        epb.packet_len,
        &key,
    );""",
)
staging.write_text(text)

# Bug 4: unique timestamp packet_count
summary = root / "export/summary.rs"
text = summary.read_text()
text = text.replace(
    "    let packet_count: usize = interfaces.iter().map(|i| i.packet_count).sum();",
    """    let mut unique_ts = std::collections::HashSet::new();
    for pkt in &packets {
        unique_ts.insert(pkt.ts_ns);
    }
    let packet_count = unique_ts.len();""",
)
summary.write_text(text)

# Bug 5: full replay key
dedup = root / "index/dedup.rs"
dedup.write_text(
    """pub fn replay_key(interface_id: u32, ts_ns: u64, file_offset: u64) -> String {
    format!("{interface_id}:{ts_ns}:{file_offset}")
}
"""
)
PY

export CARGO_INCREMENTAL=0
/usr/local/cargo/bin/cargo build --release --locked
mkdir -p /app/bin
cp /app/target/release/pcap-index /app/bin/pcap-index
