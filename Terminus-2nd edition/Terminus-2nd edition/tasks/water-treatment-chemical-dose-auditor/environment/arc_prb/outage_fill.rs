pub const MAX_FORWARD_FILL: u32 = 3;

pub fn forward_fill(values: &[Option<f64>]) -> Vec<f64> {
    values
        .iter()
        .map(|v| v.unwrap_or(0.0))
        .collect()
}
