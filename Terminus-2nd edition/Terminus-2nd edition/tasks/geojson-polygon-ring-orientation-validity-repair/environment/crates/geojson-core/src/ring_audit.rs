//! Legacy ring metrics helpers — not used by the repair export hot path.

use crate::types::Ring;
use crate::area::signed_area;

pub fn ring_perimeter(ring: &Ring) -> f64 {
    if ring.len() < 2 {
        return 0.0;
    }
    let mut total = 0.0;
    for i in 0..ring.len() - 1 {
        let dx = ring[i + 1][0] - ring[i][0];
        let dy = ring[i + 1][1] - ring[i][1];
        total += (dx * dx + dy * dy).sqrt();
    }
    total
}

pub fn compactness(ring: &Ring) -> f64 {
    let area = signed_area(ring).abs();
    if area <= 0.0 {
        return 0.0;
    }
    let perimeter = ring_perimeter(ring);
    if perimeter <= 0.0 {
        return 0.0;
    }
    4.0 * std::f64::consts::PI * area / (perimeter * perimeter)
}
