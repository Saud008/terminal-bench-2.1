pub fn attenuate(source_ppv: f64, distance_m: f64, reference_m: f64, exponent: f64) -> f64 {
    if distance_m <= 0.0 {
        return source_ppv;
    }
    source_ppv * (reference_m / distance_m).powf(exponent)
}
