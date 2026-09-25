use crate::ingest::{read_i32_le, read_u32_le};
use crate::types::RootDiscovery;

pub fn discover_roots(wire: &[u8]) -> Result<Vec<RootDiscovery>, String> {
    if wire.len() < 4 {
        return Err("wire too short for root".into());
    }
    if wire.len() >= 12 && wire[wire.len() - 12..wire.len() - 8] == *crate::MULTI_ROOT_MAGIC {
        return discover_multi_root(wire);
    }
    let root_uoff = read_u32_le(wire, wire.len() - 4).ok_or("missing root footer")?;
    let table_off = wire.len() - 4 - root_uoff as usize;
    discover_from_table(wire, table_off as u32)
}

fn discover_multi_root(wire: &[u8]) -> Result<Vec<RootDiscovery>, String> {
    let secondary_u = read_u32_le(wire, wire.len() - 8).ok_or("bad secondary root")?;
    let primary_u = read_u32_le(wire, wire.len() - 4).ok_or("bad primary root")?;
    let primary_off = wire.len() - 12 - primary_u as usize;
    let secondary_off = wire.len() - 12 - secondary_u as usize;
    let mut roots = Vec::new();
    roots.push(discover_from_table(wire, primary_off as u32)?[0].clone());
    roots.push(discover_from_table(wire, secondary_off as u32)?[0].clone());
    Ok(roots)
}

fn discover_from_table(wire: &[u8], table_off: u32) -> Result<Vec<RootDiscovery>, String> {
    let off = table_off as usize;
    if off + 4 > wire.len() {
        return Err("table offset out of range".into());
    }
    let soffset = read_i32_le(wire, off).ok_or("missing vtable soffset")?;
    let vtable_off = (off as i64 + soffset as i64) as usize;
    if !field_presence_ready(wire, vtable_off) {
        return Err("field presence not ready".into());
    }
    if vtable_off + 4 > wire.len() {
        return Err("vtable out of range".into());
    }
    Ok(vec![RootDiscovery {
        table_off,
        vtable_off: vtable_off as u32,
    }])
}

fn field_presence_ready(wire: &[u8], vtable_off: usize) -> bool {
    if vtable_off + 4 > wire.len() {
        return false;
    }
    let vtable_len = u16::from_le_bytes(wire[vtable_off..vtable_off + 2].try_into().unwrap());
    if vtable_len < 4 {
        return false;
    }
    if vtable_off + 6 > wire.len() {
        return false;
    }
    let slot0 = u16::from_le_bytes(wire[vtable_off + 4..vtable_off + 6].try_into().unwrap());
    slot0 != 0
}
