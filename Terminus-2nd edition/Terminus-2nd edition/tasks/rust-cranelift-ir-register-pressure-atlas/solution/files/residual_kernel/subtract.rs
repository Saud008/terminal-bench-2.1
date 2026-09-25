use crate::fluence_models::BackgroundAnchor;

/// Piecewise-linear background estimate at `energy_kev`, flat-extrapolated outside the anchor
/// range.
pub fn background_at(energy_kev: f64, anchors: &[BackgroundAnchor]) -> f64 {
    if anchors.is_empty() {
        return 0.0;
    }
    let mut sorted: Vec<&BackgroundAnchor> = anchors.iter().collect();
    sorted.sort_by(|a, b| a.energy_kev.partial_cmp(&b.energy_kev).unwrap());
    let last = sorted.len() - 1;
    if energy_kev <= sorted[0].energy_kev {
        return sorted[0].counts;
    }
    if energy_kev >= sorted[last].energy_kev {
        return sorted[last].counts;
    }
    for i in 0..last {
        let a = sorted[i];
        let b = sorted[i + 1];
        if energy_kev >= a.energy_kev && energy_kev <= b.energy_kev {
            if (b.energy_kev - a.energy_kev).abs() < f64::EPSILON {
                return a.counts;
            }
            let frac = (energy_kev - a.energy_kev) / (b.energy_kev - a.energy_kev);
            return a.counts + (b.counts - a.counts) * frac;
        }
    }
    sorted[last].counts
}

pub fn residual_counts(measured_counts: f64, energy_kev: f64, anchors: &[BackgroundAnchor]) -> f64 {
    crate::round6(measured_counts - background_at(energy_kev, anchors))
}
