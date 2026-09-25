use crate::types::{GapSpan, WireEntry};

pub fn compact_without_gaps(wire: &[u8], _gaps: &[GapSpan]) -> Vec<u8> {
    wire.to_vec()
}

pub fn restore_gaps(out: &mut Vec<u8>, entry: &WireEntry) -> Result<(), String> {
    for gap in &entry.gaps {
        let start = gap.start as usize;
        let end = start + gap.length as usize;
        if end <= entry.wire.len() && end <= out.len() {
            out[start..end].copy_from_slice(&entry.wire[start..end]);
        }
    }
    Ok(())
}
