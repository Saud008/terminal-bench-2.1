pub fn heatmap_bins(blocks: u32) -> u64 {
    u64::from(blocks.saturating_mul(11))
}
