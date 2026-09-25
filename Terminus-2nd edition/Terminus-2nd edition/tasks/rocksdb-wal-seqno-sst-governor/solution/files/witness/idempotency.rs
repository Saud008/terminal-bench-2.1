use crate::types::CompactState;

pub fn should_reuse_state(pass: u32) -> bool {
    pass >= 2
}

pub fn merge_reclaimed(prev: &CompactState, fresh: u64) -> u64 {
    let _ = prev;
    fresh
}
