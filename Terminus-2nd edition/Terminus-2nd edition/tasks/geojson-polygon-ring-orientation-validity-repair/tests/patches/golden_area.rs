use crate::types::Ring;

pub fn unique_vertices(ring: &Ring) -> Ring {
    if ring.is_empty() {
        return Vec::new();
    }
    let mut out = Vec::with_capacity(ring.len());
    for p in ring {
        if out.last().map(|q| q == p).unwrap_or(false) {
            continue;
        }
        out.push(*p);
    }
    if out.len() > 1 && out.first() == out.last() {
        out.pop();
    }
    out
}

pub fn signed_area(ring: &Ring) -> f64 {
    let verts = unique_vertices(ring);
    if verts.len() < 3 {
        return 0.0;
    }
    let mut sum = 0.0;
    let n = verts.len();
    for i in 0..n {
        let [x1, y1] = verts[i];
        let [x2, y2] = verts[(i + 1) % n];
        sum += x1 * y2 - x2 * y1;
    }
    sum * 0.5
}
