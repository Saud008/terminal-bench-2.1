use crate::types::{GapSpan, WireEntry};

pub fn compact_without_gaps(wire: &[u8], gaps: &[GapSpan]) -> Vec<u8> {
    if gaps.is_empty() {
        return wire.to_vec();
    }
    let mut out = Vec::new();
    let mut cursor = 0usize;
    for gap in gaps {
        let start = gap.start as usize;
        let end = start + gap.length as usize;
        if start > cursor {
            out.extend_from_slice(&wire[cursor..start]);
        }
        cursor = end;
    }
    if cursor < wire.len() {
        out.extend_from_slice(&wire[cursor..]);
    }
    out
}

pub fn restore_gaps(_out: &mut Vec<u8>, _entry: &WireEntry) -> Result<(), String> {
    Ok(())
}
