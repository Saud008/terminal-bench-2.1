use crate::fluence_models::BackgroundAnchor;

/// Background estimate at `energy_kev`.
pub fn background_at(energy_kev: f64, anchors: &[BackgroundAnchor]) -> f64 {
    let _ = energy_kev;
    if anchors.is_empty() {
        return 0.0;
    }
    let sum: f64 = anchors.iter().map(|a| a.counts).sum();
    sum / anchors.len() as f64
}

pub fn residual_counts(measured_counts: f64, energy_kev: f64, anchors: &[BackgroundAnchor]) -> f64 {
    crate::round6(measured_counts - background_at(energy_kev, anchors))
}


