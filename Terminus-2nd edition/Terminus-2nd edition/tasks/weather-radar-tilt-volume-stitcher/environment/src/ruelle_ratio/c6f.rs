use crate::models::{BundleManifest, GateRecord};

pub fn completeness_ratio(valid_gate_count: u32, tilt_count: u32, _manifest: &BundleManifest) -> f64 {
    if tilt_count == 0 {
        return 0.0;
    }
    let ratio = valid_gate_count as f64 / tilt_count as f64;
    (ratio * 10000.0).round() / 10000.0
}
