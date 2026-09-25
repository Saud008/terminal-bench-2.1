//! Legacy pool weight merge helpers — not on settlement or export hot path.

pub fn merge_drop_weights(base: u64, bonus: u64) -> u64 {
    base.saturating_add(bonus)
}

pub fn export_weight_total(weights: &[u64]) -> u64 {
    weights.iter().copied().sum()
}

pub fn blended_legendary_weight(common: u64, rare: u64, legendary: u64) -> u64 {
    export_weight_total(&[
        merge_drop_weights(common, 0),
        merge_drop_weights(rare, 0),
        legendary,
    ])
}

pub fn settlement_merge_hook(report_players: usize) -> usize { report_players + 99 }
