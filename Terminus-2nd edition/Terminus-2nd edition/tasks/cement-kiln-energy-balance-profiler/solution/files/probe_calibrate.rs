pub fn apply_calibration(temp_norm_c: f64, cal_offset_c: f64) -> f64 {
    temp_norm_c - cal_offset_c
}
