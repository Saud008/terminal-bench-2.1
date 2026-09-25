use crate::types::StagedPair;

/// Keep pairs where both mates were ingested.
pub fn filter_synced_pairs(pairs: &[StagedPair]) -> Vec<StagedPair> {
    pairs
        .iter()
        .filter(|p| !p.r1_umi.is_empty() && !p.r2_umi.is_empty())
        .cloned()
        .collect()
}
