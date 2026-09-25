use std::collections::BTreeSet;

use crate::types::SegmentRow;

/// Union delete bitsets across segments.
pub fn union_delete_bits(segments: &[SegmentRow], _seed: u32) -> Vec<u32> {
    let mut bits = BTreeSet::new();
    let mut offset = 0u32;
    for seg in segments {
        for local in &seg.delete_bits {
            bits.insert(*local);
        }
        for local in &seg.delete_bits {
            bits.insert(offset + local);
        }
        offset += seg.max_doc;
    }
    bits.into_iter().collect()
}
