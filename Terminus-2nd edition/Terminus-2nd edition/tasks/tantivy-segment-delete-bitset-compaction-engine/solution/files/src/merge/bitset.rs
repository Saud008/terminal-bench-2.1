use std::collections::BTreeSet;

use crate::merge::engine::remap_local_doc;
use crate::types::SegmentRow;

pub fn union_delete_bits(segments: &[SegmentRow], seed: u32) -> Vec<u32> {
    let mut bits = BTreeSet::new();
    let mut offset = 0u32;
    for seg in segments {
        for local in &seg.delete_bits {
            let remapped = remap_local_doc(*local, seg.max_doc, seed);
            bits.insert(offset + remapped);
        }
        offset += seg.max_doc;
    }
    bits.into_iter().collect()
}
