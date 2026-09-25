/// Quantize a value at the micron-eV scale.
pub fn quantize(v: f64, scale: i64) -> f64 {
    let s = scale as f64;
    (v * s).trunc() / s
}


