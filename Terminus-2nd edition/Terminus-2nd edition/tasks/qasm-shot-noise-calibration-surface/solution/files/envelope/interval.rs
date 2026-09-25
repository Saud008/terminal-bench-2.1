use crate::types::IntervalBin;

pub fn wilson_intervals(probs: &[f64], total_shots: u64, _source_probs: &[f64]) -> Vec<IntervalBin> {
    let n = total_shots as f64;
    let z = 1.96;
    probs
        .iter()
        .map(|&p| {
            let half = if n > 0.0 {
                (z / (2.0 * n)) * (4.0 * n * p * (1.0 - p) + z * z).sqrt()
                    / (1.0 + (z * z) / n)
            } else {
                0.0
            };
            let lower = (p - half).max(0.0);
            let upper = (p + half).min(1.0);
            IntervalBin {
                lower: (lower * 1_000_000.0).round() / 1_000_000.0,
                upper: (upper * 1_000_000.0).round() / 1_000_000.0,
            }
        })
        .collect()
}
