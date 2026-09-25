use std::fs;
use std::path::Path;

use serde::Serialize;

use crate::db::PacketRow;

pub const INDEX_PATH: &str = "/app/state/pcap.idx";

#[derive(Serialize)]
struct IndexLine {
    cap_len: u32,
    file_offset: u64,
    interface_id: u32,
    packet_len: u32,
    ts_ns: u64,
}

pub fn write_index(rows: &[PacketRow]) -> Result<(), String> {
    let parent = Path::new(INDEX_PATH).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let mut lines = Vec::new();
    for row in rows {
        let obj = IndexLine {
            cap_len: row.cap_len,
            file_offset: row.file_offset,
            interface_id: row.interface_id,
            packet_len: row.packet_len,
            ts_ns: row.ts_ns,
        };
        let line = serde_json::to_string(&obj).map_err(|e| e.to_string())?;
        lines.push(line);
    }
    let body = lines.join("\n");
    fs::write(INDEX_PATH, body).map_err(|e| e.to_string())
}
