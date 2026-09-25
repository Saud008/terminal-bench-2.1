use std::collections::BTreeMap;

/// Coordinate labels derived from chunk origin and dataset attributes.
pub fn coord_labels(
    origin: &[u64],
    _chunk_dims: &[u64],
    attrs: &BTreeMap<String, serde_json::Value>,
) -> Vec<f64> {
    if origin.is_empty() {
        return Vec::new();
    }
    let scale = attrs
        .get("scale")
        .and_then(|v| v.as_f64())
        .unwrap_or(1.0);
    origin.iter().map(|o| (*o as f64) * scale).collect()
}

pub fn coord_consistent(origin: &[u64], index_origin: &[u64], labels: &[f64]) -> bool {
    if origin.len() != index_origin.len() || origin.len() != labels.len() {
        return false;
    }
    origin
        .iter()
        .zip(index_origin.iter())
        .all(|(a, b)| a == b)
        && labels.iter().all(|v| v.is_finite())
}
