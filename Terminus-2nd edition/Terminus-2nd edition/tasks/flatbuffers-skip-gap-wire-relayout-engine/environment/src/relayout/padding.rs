use crate::types::WireEntry;

pub fn apply_padding_before_fixup(out: &mut Vec<u8>, entry: &WireEntry) -> Result<(), String> {
    if entry.roots.is_empty() {
        return Ok(());
    }
    let align = 8usize;
    let pad = (align - (out.len() % align)) % align;
    if pad > 0 {
        out.extend(std::iter::repeat(0u8).take(pad));
    }
    let root = &entry.roots[0];
    if (root.table_off as usize) + 4 <= out.len() {
        let soffset: i32 = (root.vtable_off as i32) - (root.table_off as i32);
        let off = root.table_off as usize;
        out[off..off + 4].copy_from_slice(&soffset.to_le_bytes());
    }
    Ok(())
}
