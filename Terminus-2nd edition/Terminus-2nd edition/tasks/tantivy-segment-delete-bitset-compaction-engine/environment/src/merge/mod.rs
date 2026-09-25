pub mod bitset;
pub mod engine;
pub mod freqs;
pub mod postings;
pub mod stats;

use crate::types::{MergedTerm, SegmentRow, SegmentStats};

pub fn merge_segments(segments: &[SegmentRow], pass: u32, seed: u32) -> SegmentStats {
    let delete_bits = bitset::union_delete_bits(segments, seed);
    let term_map = freqs::rollup_term_freqs(segments);
    let live_max_doc = stats::live_max_doc(segments);
    let mut terms: Vec<MergedTerm> = term_map
        .into_iter()
        .map(|((field, term), (freq, norm))| MergedTerm {
            field,
            term,
            freq,
            norm: postings::export_norm(norm),
        })
        .collect();
    terms.sort_by(|a, b| {
        (&a.field, &a.term)
            .cmp(&(&b.field, &b.term))
    });
    SegmentStats {
        live_max_doc,
        delete_bits,
        terms,
        merge_pass: pass,
    }
}
