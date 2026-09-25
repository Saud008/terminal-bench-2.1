use crate::types::CompactState;

pub fn should_reuse_state(pass: u32) -> bool {
    pass >= 2
}

/// Combine prior and fresh reclaimed byte totals across passes.
pub fn merge_reclaimed(prev: &CompactState, fresh: u64) -> u64 {
    prev.reclaimed_bytes + fresh
}
