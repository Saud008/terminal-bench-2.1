/// Quantize a residual coordinate at microdegree_scale (truncate toward zero).
pub fn quantize_coord(v: f64, scale: i64) -> f64 {
    let s = scale as f64;
    if s == 0.0 {
        return 0.0;
    }
    let scaled = v * s;
    let toward_zero = if scaled < 0.0 {
        scaled.ceil()
    } else {
        scaled.floor()
    };
    toward_zero / s
}
