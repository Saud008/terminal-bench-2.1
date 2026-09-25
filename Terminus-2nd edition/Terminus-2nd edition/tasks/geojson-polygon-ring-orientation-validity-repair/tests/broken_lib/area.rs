use crate::types::Ring;

pub fn signed_area(ring: &Ring) -> f64 {
    if ring.len() < 3 {
        return 0.0;
    }
    let mut sum = 0.0;
    for i in 0..ring.len() - 1 {
        let [x1, y1] = ring[i];
        let [x2, y2] = ring[i + 1];
        sum += x1 * y2 - x2 * y1;
    }
    sum * 0.5
}

pub fn unique_vertices(ring: &Ring) -> Ring {
    ring.clone()
}
