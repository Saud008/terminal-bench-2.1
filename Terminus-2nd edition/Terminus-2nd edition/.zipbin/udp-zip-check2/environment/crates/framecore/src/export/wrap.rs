//! Legacy range merge helper kept for an older report format.

use crate::model::GapRange;

/// Merge helper used by the pre-staging report format: sorts by descending start only.
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
