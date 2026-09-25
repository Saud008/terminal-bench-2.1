use crate::types::DatumOffset;

/// Residual vertices relative to the campaign datum offset.
pub fn apply_residual(vertices: &[[f64; 2]], datum: &DatumOffset) -> Vec<[f64; 2]> {
    vertices
        .iter()
        .map(|v| [v[0] - datum.lon, v[1] - datum.lat])
        .collect()
}
