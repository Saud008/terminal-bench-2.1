use std::fs;
use std::io::Read;

use crate::types::{GapSpan, LedgerFile, RootRecord, WireEntry};

pub fn load_ledger(path: &str) -> Result<LedgerFile, String> {
    let mut f = fs::File::open(path).map_err(|e| e.to_string())?;
    let mut buf = Vec::new();
    f.read_to_end(&mut buf).map_err(|e| e.to_string())?;
    parse_ledger(&buf)
}

pub fn save_ledger(path: &str, ledger: &LedgerFile) -> Result<(), String> {
    let parent = std::path::Path::new(path).parent().unwrap_or(std::path::Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let bytes = encode_ledger(ledger)?;
    fs::write(path, bytes).map_err(|e| e.to_string())
}

pub fn parse_ledger(buf: &[u8]) -> Result<LedgerFile, String> {
    if buf.len() < 12 || &buf[0..4] != crate::LEDGER_MAGIC {
        return Err("bad ledger magic".into());
    }
    let mut off = 4usize;
    let _version = read_u32(buf, &mut off)?;
    let ingest_seq = read_u32(buf, &mut off)?;
    let count = read_u32(buf, &mut off)? as usize;
    let mut entries = Vec::with_capacity(count);
    for _ in 0..count {
        entries.push(read_entry(buf, &mut off)?);
    }
    Ok(LedgerFile { ingest_seq, entries })
}

fn read_entry(buf: &[u8], off: &mut usize) -> Result<WireEntry, String> {
    let name_len = read_u32(buf, off)? as usize;
    let name = read_string(buf, off, name_len)?;
    let wire_len = read_u32(buf, off)? as usize;
    let wire = read_bytes(buf, off, wire_len)?;
    let root_count = read_u32(buf, off)? as usize;
    let mut roots = Vec::with_capacity(root_count);
    for _ in 0..root_count {
        roots.push(read_root(buf, off)?);
    }
    let gap_count = read_u32(buf, off)? as usize;
    let mut gaps = Vec::with_capacity(gap_count);
    for _ in 0..gap_count {
        gaps.push(GapSpan {
            start: read_u32(buf, off)?,
            length: read_u32(buf, off)?,
        });
    }
    Ok(WireEntry {
        name,
        wire,
        roots,
        gaps,
    })
}

fn read_root(buf: &[u8], off: &mut usize) -> Result<RootRecord, String> {
    let table_off = read_u32(buf, off)?;
    let vtable_off = read_u32(buf, off)?;
    let vtable_len = read_u16(buf, off)?;
    let object_size = read_u16(buf, off)?;
    let slot_count = read_u32(buf, off)? as usize;
    let mut slots = Vec::with_capacity(slot_count);
    for _ in 0..slot_count {
        slots.push(read_u32(buf, off)?);
    }
    Ok(RootRecord {
        table_off,
        vtable_off,
        vtable_len,
        object_size,
        slots,
    })
}

pub fn encode_ledger(ledger: &LedgerFile) -> Result<Vec<u8>, String> {
    let mut out = Vec::new();
    out.extend_from_slice(crate::LEDGER_MAGIC);
    write_u32(&mut out, 1);
    write_u32(&mut out, ledger.ingest_seq);
    write_u32(&mut out, ledger.entries.len() as u32);
    for entry in &ledger.entries {
        write_entry(&mut out, entry)?;
    }
    Ok(out)
}

fn write_entry(out: &mut Vec<u8>, entry: &WireEntry) -> Result<(), String> {
    let name_bytes = entry.name.as_bytes();
    write_u32(out, name_bytes.len() as u32);
    out.extend_from_slice(name_bytes);
    write_u32(out, entry.wire.len() as u32);
    out.extend_from_slice(&entry.wire);
    write_u32(out, entry.roots.len() as u32);
    for root in &entry.roots {
        write_root(out, root);
    }
    write_u32(out, entry.gaps.len() as u32);
    for gap in &entry.gaps {
        write_u32(out, gap.start);
        write_u32(out, gap.length);
    }
    Ok(())
}

fn write_root(out: &mut Vec<u8>, root: &RootRecord) {
    write_u32(out, root.table_off);
    write_u32(out, root.vtable_off);
    write_u16(out, root.vtable_len);
    write_u16(out, root.object_size);
    write_u32(out, root.slots.len() as u32);
    for slot in &root.slots {
        write_u32(out, *slot);
    }
}

fn read_u32(buf: &[u8], off: &mut usize) -> Result<u32, String> {
    if *off + 4 > buf.len() {
        return Err("ledger truncated".into());
    }
    let v = u32::from_le_bytes(buf[*off..*off + 4].try_into().unwrap());
    *off += 4;
    Ok(v)
}

fn read_u16(buf: &[u8], off: &mut usize) -> Result<u16, String> {
    if *off + 2 > buf.len() {
        return Err("ledger truncated".into());
    }
    let v = u16::from_le_bytes(buf[*off..*off + 2].try_into().unwrap());
    *off += 2;
    Ok(v)
}

fn read_string(buf: &[u8], off: &mut usize, len: usize) -> Result<String, String> {
    if *off + len > buf.len() {
        return Err("ledger truncated".into());
    }
    let s = std::str::from_utf8(&buf[*off..*off + len]).map_err(|e| e.to_string())?;
    *off += len;
    Ok(s.to_string())
}

fn read_bytes(buf: &[u8], off: &mut usize, len: usize) -> Result<Vec<u8>, String> {
    if *off + len > buf.len() {
        return Err("ledger truncated".into());
    }
    let v = buf[*off..*off + len].to_vec();
    *off += len;
    Ok(v)
}

fn write_u32(out: &mut Vec<u8>, v: u32) {
    out.extend_from_slice(&v.to_le_bytes());
}

fn write_u16(out: &mut Vec<u8>, v: u16) {
    out.extend_from_slice(&v.to_le_bytes());
}
