use crate::types::VtableHeader;

pub fn read_vtable_header(wire: &[u8], vtable_off: usize) -> Result<VtableHeader, String> {
    if vtable_off + 4 > wire.len() {
        return Err("vtable header out of range".into());
    }
    let b0: [u8; 2] = wire[vtable_off..vtable_off + 2].try_into().map_err(|_| "vtable")?;
    let b1: [u8; 2] = wire[vtable_off + 2..vtable_off + 4]
        .try_into()
        .map_err(|_| "vtable")?;
    Ok(VtableHeader {
        vtable_len: u16::from_le_bytes(b0),
        object_size: u16::from_le_bytes(b1),
    })
}

pub fn decode_vtable_slots(wire: &[u8], vtable_off: usize, vtable_len: u16) -> Result<Vec<u32>, String> {
    let slot_bytes = vtable_len.saturating_sub(4) as usize;
    let slot_count = slot_bytes / 2;
    let mut slots = Vec::with_capacity(slot_count);
    let mut off = vtable_off + 4;
    for _ in 0..slot_count {
        if off + 2 > wire.len() {
            break;
        }
        let b: [u8; 2] = wire[off..off + 2].try_into().unwrap();
        let voff = u16::from_le_bytes(b);
        slots.push(if voff == 0 { 0 } else { voff as u32 });
        off += 2;
    }
    Ok(slots)
}
