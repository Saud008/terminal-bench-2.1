use crate::types::SegmentStats;

/// Export-side stats envelope (separate from merge engine crate).
pub fn attach_merge_pass(mut stats: SegmentStats, pass: u32) -> SegmentStats {
    stats.merge_pass = pass;
    stats
}

pub fn term_count(stats: &SegmentStats) -> usize {
    stats.terms.len()
}
