use crate::types::PropertyParcel;

pub fn compliance_distance(
    blast_e: f64,
    blast_n: f64,
    parcel: &PropertyParcel,
    _sensor_e: f64,
    _sensor_n: f64,
) -> f64 {
    let mut best = f64::MAX;
    for v in &parcel.boundary_vertices {
        let dx = blast_e - v[0];
        let dy = blast_n - v[1];
        let d = (dx * dx + dy * dy).sqrt();
        if d < best {
            best = d;
        }
    }
    best
}
