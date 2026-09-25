/// Quantize a residual coordinate at microdegree_scale.
pub fn quantize_coord(v: f64, scale: i64) -> f64 {
    let s = scale as f64;
    (v * s).ceil() / s
}
