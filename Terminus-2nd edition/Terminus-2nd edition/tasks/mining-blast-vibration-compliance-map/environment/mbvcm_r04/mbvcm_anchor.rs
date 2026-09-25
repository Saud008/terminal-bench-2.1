use crate::types::PropertyParcel;

pub fn compliance_distance(
    blast_e: f64,
    blast_n: f64,
    parcel: &PropertyParcel,
    _sensor_e: f64,
    _sensor_n: f64,
) -> f64 {
    let mut sum_e = 0.0;
    let mut sum_n = 0.0;
    let n = parcel.boundary_vertices.len() as f64;
    for v in &parcel.boundary_vertices {
        sum_e += v[0];
        sum_n += v[1];
    }
    let cx = sum_e / n;
    let cy = sum_n / n;
    let dx = blast_e - cx;
    let dy = blast_n - cy;
    (dx * dx + dy * dy).sqrt()
}
