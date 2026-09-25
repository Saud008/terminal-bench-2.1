use std::collections::HashMap;

use crate::types::SegmentRow;

pub fn rollup_term_freqs(segments: &[SegmentRow]) -> HashMap<(String, String), (u32, u8)> {
    let mut out: HashMap<(String, String), (u32, u8)> = HashMap::new();
    for seg in segments {
        for row in &seg.terms {
            let key = (row.field.clone(), row.term.clone());
            let live = row.freq.saturating_sub(row.deleted_hits);
            let entry = out.entry(key).or_insert((0, row.norm));
            entry.0 += live;
            entry.1 = row.norm;
        }
    }
    out
}
