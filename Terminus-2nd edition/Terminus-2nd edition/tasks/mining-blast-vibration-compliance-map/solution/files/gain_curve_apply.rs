pub fn apply_calibration(raw_ppv: f64, zero_offset: f64, gain: f64) -> f64 {
    (raw_ppv - zero_offset) * gain
}
