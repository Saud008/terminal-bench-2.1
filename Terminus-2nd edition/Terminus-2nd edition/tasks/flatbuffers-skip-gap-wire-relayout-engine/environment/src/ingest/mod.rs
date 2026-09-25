use std::fs;

use crate::staging;
use crate::types::{GapSpan, LedgerFile, RootRecord, WireEntry};

pub fn ingest_directory(dir: &str, ledger_path: &str) -> Result<(), String> {
    let mut paths: Vec<_> = fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("wire"))
        .collect();
    paths.sort();

    let mut ledger = load_ledger(ledger_path).unwrap_or(LedgerFile {
        ingest_seq: 0,
        entries: Vec::new(),
    });
    ledger.ingest_seq += 1;

    for path in paths {
        let name = path
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown.wire")
            .to_string();
        let wire = fs::read(&path).map_err(|e| e.to_string())?;
        let entry = parse_wire(&name, &wire)?;
        ledger.entries.push(entry);
    }

    save_ledger(ledger_path, &ledger)
}

pub fn parse_wire(name: &str, wire: &[u8]) -> Result<WireEntry, String> {
    if wire.len() < 8 {
        return Err(format!("wire too short: {name}"));
    }
    let gaps = scan_gaps(wire);
    let roots = crate::vtable::validate::discover_roots(wire)?;
    let mut root_records = Vec::new();
    for root in roots {
        let vtable_off = root.vtable_off as usize;
        let header = crate::vtable::decode::read_vtable_header(wire, vtable_off)?;
        let slots = crate::vtable::decode::decode_vtable_slots(wire, vtable_off, header.vtable_len)?;
        root_records.push(RootRecord {
            table_off: root.table_off,
            vtable_off: root.vtable_off,
            vtable_len: header.vtable_len,
            object_size: header.object_size,
            slots,
        });
    }
    Ok(WireEntry {
        name: name.to_string(),
        wire: wire.to_vec(),
        roots: root_records,
        gaps,
    })
}

pub fn scan_gaps(wire: &[u8]) -> Vec<GapSpan> {
    let mut gaps = Vec::new();
    let mut i = 0usize;
    while i + 8 <= wire.len() {
        if wire[i..i + 4] == *crate::GAP_MAGIC {
            if let Some(len) = read_u32_le(wire, i + 4) {
                let span_len = len as usize;
                if i + 8 + span_len <= wire.len() {
                    gaps.push(GapSpan {
                        start: i as u32,
                        length: (8 + span_len) as u32,
                    });
                    i += 8 + span_len;
                    continue;
                }
            }
        }
        i += 1;
    }
    gaps
}

pub fn read_u32_le(buf: &[u8], off: usize) -> Option<u32> {
    if off + 4 > buf.len() {
        return None;
    }
    let b: [u8; 4] = buf[off..off + 4].try_into().ok()?;
    Some(u32::from_le_bytes(b))
}

pub fn read_u16_le(buf: &[u8], off: usize) -> Option<u16> {
    if off + 2 > buf.len() {
        return None;
    }
    let b: [u8; 2] = buf[off..off + 2].try_into().ok()?;
    Some(u16::from_le_bytes(b))
}

pub fn read_i32_le(buf: &[u8], off: usize) -> Option<i32> {
    read_u32_le(buf, off).map(|v| v as i32)
}

pub fn load_ledger(path: &str) -> Result<LedgerFile, String> {
    staging::load_ledger(path)
}

pub fn save_ledger(path: &str, ledger: &LedgerFile) -> Result<(), String> {
    staging::save_ledger(path, ledger)
}
