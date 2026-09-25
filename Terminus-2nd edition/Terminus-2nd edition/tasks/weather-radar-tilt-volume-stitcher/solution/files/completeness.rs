use crate::models::{BundleManifest, StagedGate};

pub fn completeness_ratio(
    valid_gate_count: u32,
    tilt_count: u32,
    manifest: &BundleManifest,
) -> f64 {
    let expected = manifest
        .expected_ray_count
        .saturating_mul(manifest.expected_gate_bins)
        .saturating_mul(tilt_count);
    if expected == 0 {
        return 0.0;
    }
    let ratio = valid_gate_count as f64 / expected as f64;
    (ratio * 10000.0).round() / 10000.0
}
