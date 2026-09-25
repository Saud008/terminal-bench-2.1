use crate::types::{PolygonCoords, Ring};
use crate::area::signed_area;

pub fn point_in_ring(pt: [f64; 2], ring: &Ring) -> bool {
    let mut inside = false;
    let mut j = ring.len().saturating_sub(1);
    for i in 0..ring.len() {
        let [xi, yi] = ring[i];
        let [xj, yj] = ring[j];
        let intersect = ((yi > pt[1]) != (yj > pt[1]))
            && (pt[0] < (xj - xi) * (pt[1] - yi) / ((yj - yi).abs().max(1e-12)) + xi);
        if intersect {
            inside = !inside;
        }
        j = i;
    }
    inside
}

pub fn ring_representative(ring: &Ring) -> [f64; 2] {
    if ring.is_empty() {
        return [0.0, 0.0];
    }
    let mut sx = 0.0;
    let mut sy = 0.0;
    let n = ring.len().saturating_sub(1).max(1);
    for p in ring.iter().take(n) {
        sx += p[0];
        sy += p[1];
    }
    [sx / n as f64, sy / n as f64]
}

pub fn nest_polygon(rings: PolygonCoords) -> (PolygonCoords, u32) {
    if rings.len() <= 1 {
        return (rings, 0);
    }
    let mut tagged: Vec<(usize, f64, Ring)> = rings
        .into_iter()
        .enumerate()
        .map(|(i, r)| (i, signed_area(&r).abs(), r))
        .collect();
    tagged.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    let exterior = tagged[0].2.clone();
    let mut holes: Vec<Ring> = Vec::new();
    for (_i, _area, ring) in tagged.into_iter().skip(1) {
        let rep = ring_representative(&ring);
        if point_in_ring(rep, &exterior) {
            holes.push(ring);
        }
    }
    let mut out = vec![exterior];
    out.extend(holes);
    let reordered = if out.len() > 1 { 1 } else { 0 };
    (out, reordered)
}
