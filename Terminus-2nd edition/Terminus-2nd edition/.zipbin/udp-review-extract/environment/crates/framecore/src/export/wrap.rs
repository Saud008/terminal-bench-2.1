//! Legacy range merge helper — not used by the export hot path.

use crate::model::GapRange;

/// Decoy merge: sorts by descending start only. Do not call from publish.
pub fn merge_ranges_legacy(raw: &[(u32, u32)]) -> Vec<GapRange> {
    if raw.is_empty() {
        return Vec::new();
    }
    let mut pairs = raw.to_vec();
    pairs.sort_by(|a, b| b.0.cmp(&a.0));
    pairs
        .into_iter()
        .map(|(start, end)| GapRange { start, end })
        .collect()
}
