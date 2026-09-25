use crate::types::MergeState;

pub fn should_reuse_state(pass: u32) -> bool {
    pass >= 2
}

pub fn merge_delete_bits(prev: &MergeState, fresh: &[u32]) -> Vec<u32> {
    let mut combined = prev.delete_bits.clone();
    combined.extend_from_slice(fresh);
    combined.sort_unstable();
    combined.dedup();
    combined
}
