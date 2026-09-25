use anyhow::{bail, Result};

use crate::kx42::{read_i32, read_u16};

/// Map a table object to its vtable anchor in a finished buffer.
fn table_to_vtable(table: usize, soff: i32) -> usize {
    (table as i64 + soff as i64) as usize
}

pub fn vtable_pos(buf: &[u8], table: usize) -> Result<usize> {
    let soff = read_i32(buf, table)?;
    if soff == 0 {
        bail!("missing vtable offset at table {table}");
    }
    let vt = table_to_vtable(table, soff);
    if vt + 4 > buf.len() {
        bail!("vtable out of range");
    }
    Ok(vt)
}

pub fn vtable_field_abs(buf: &[u8], table: usize, slot: usize) -> Result<usize> {
    let vt = vtable_pos(buf, table)?;
    let vtable_size = read_u16(buf, vt)? as usize;
    let entry = vt + 4 + slot * 2;
    if entry + 2 > vt + vtable_size {
        bail!("vtable slot {slot} unavailable");
    }
    let field_off = read_u16(buf, entry)?;
    if field_off == 0 {
        bail!("absent field slot {slot}");
    }
    Ok(table.wrapping_sub(field_off as usize))
}
