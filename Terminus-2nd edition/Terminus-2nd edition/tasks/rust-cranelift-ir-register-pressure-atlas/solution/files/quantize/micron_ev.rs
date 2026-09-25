/// Quantize a value at the micron-eV scale using round-half-away-from-zero.
pub fn quantize(v: f64, scale: i64) -> f64 {
    let s = scale as f64;
    let scaled = v * s;
    let rounded = if scaled >= 0.0 {
        (scaled + 0.5).floor()
    } else {
        (scaled - 0.5).ceil()
    };
    rounded / s
}
