use std::fs::File;
use std::io::Read;

use crate::db::Store;
use crate::index::{replay_key, write_index};
use crate::parse::block::{body_len, next_block_offset};
use crate::parse::crc::epb_core_crc_ok;
use crate::parse::epb::parse_epb_body;
use crate::parse::interface::InterfaceMap;
use crate::parse::{BT_EPB, BT_IDB, BT_SHB, OPT_END, OPT_IF_NAME};

pub fn run_ingest(path: &str, store: &mut Store) -> Result<(), String> {
    let mut data = Vec::new();
    File::open(path)
        .and_then(|mut f| f.read_to_end(&mut data))
        .map_err(|e| format!("read {path}: {e}"))?;

    let mut ifaces = InterfaceMap::new();
    let mut idb_count = 0u32;
    let mut offset = 0usize;

    while offset + 8 <= data.len() {
        let block_type = u32::from_le_bytes(data[offset..offset + 4].try_into().unwrap());
        let total_len = u32::from_le_bytes(data[offset + 4..offset + 8].try_into().unwrap());
        if total_len < 12 {
            return Err(format!("bad block length at {offset}"));
        }
        let blen = body_len(total_len);
        if offset + total_len as usize > data.len() {
            return Err(format!("truncated block at {offset}"));
        }
        let body = &data[offset + 8..offset + 8 + blen];

        match block_type {
            BT_SHB => {}
            BT_IDB => {
                let name = parse_if_name(body).unwrap_or_else(|| format!("iface{idb_count}"));
                let assigned = ifaces.register(idb_count, name);
                store
                    .upsert_iface(assigned, &ifaces.all().last().unwrap().name)
                    .map_err(|e| e.to_string())?;
                idb_count += 1;
            }
            BT_EPB => {
                process_epb(store, &ifaces, body, offset as u64)?;
            }
            _ => {}
        }

        offset = next_block_offset(offset, total_len, blen);
    }

    let rows = store.all_packets().map_err(|e| e.to_string())?;
    write_index(&rows)
}

fn parse_if_name(body: &[u8]) -> Option<String> {
    let mut pos = 8usize;
    if body.len() < 2 {
        return None;
    }
    while pos + 4 <= body.len() {
        let code = u16::from_le_bytes(body[pos..pos + 2].try_into().ok()?);
        let olen = u16::from_le_bytes(body[pos + 2..pos + 4].try_into().ok()?) as usize;
        if code == OPT_END {
            break;
        }
        if pos + 4 + olen > body.len() {
            break;
        }
        if code == OPT_IF_NAME {
            let raw = &body[pos + 4..pos + 4 + olen];
            let s = String::from_utf8_lossy(raw).trim_end_matches('\0').to_string();
            return Some(s);
        }
        let opt_pad = (olen + 3) & !3;
        pos += 4 + opt_pad;
    }
    None
}

fn process_epb(
    store: &mut Store,
    ifaces: &InterfaceMap,
    body: &[u8],
    file_offset: u64,
) -> Result<(), String> {
    let (epb, core) = parse_epb_body(body)?;
    let iface = ifaces
        .resolve(epb.interface_id)
        .ok_or_else(|| format!("unknown interface {}", epb.interface_id))?;

    let key = replay_key(iface, epb.ts_ns, file_offset);
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
    }

    Ok(())
}
