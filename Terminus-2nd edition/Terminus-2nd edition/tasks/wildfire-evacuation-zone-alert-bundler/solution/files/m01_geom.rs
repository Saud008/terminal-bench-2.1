use crate::hazard_schema::Point;

fn point_in_polygon(pt: &Point, poly: &[Point]) -> bool {
    let mut inside = false;
    let n = poly.len();
    for i in 0..n {
        let p1 = &poly[i];
        let p2 = &poly[(i + 1) % n];
        if ((p1.y > pt.y) != (p2.y > pt.y))
            && (pt.x < (p2.x - p1.x) * (pt.y - p1.y) / (p2.y - p1.y + 1e-12) + p1.x)
        {
            inside = !inside;
        }
    }
    inside
}

fn segments_intersect(a1: &Point, a2: &Point, b1: &Point, b2: &Point) -> bool {
    fn orient(p: &Point, q: &Point, r: &Point) -> f64 {
        (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)
    }
    fn on_seg(p: &Point, q: &Point, r: &Point) -> bool {
        q.x >= p.x.min(r.x) && q.x <= p.x.max(r.x) && q.y >= p.y.min(r.y) && q.y <= p.y.max(r.y)
    }
    let o1 = orient(a1, a2, b1);
    let o2 = orient(a1, a2, b2);
    let o3 = orient(b1, b2, a1);
    let o4 = orient(b1, b2, a2);
    if o1 * o2 < 0.0 && o3 * o4 < 0.0 {
        return true;
    }
    if o1.abs() < 1e-12 && on_seg(a1, b1, a2) {
        return true;
    }
    if o2.abs() < 1e-12 && on_seg(a1, b2, a2) {
        return true;
    }
    if o3.abs() < 1e-12 && on_seg(b1, a1, b2) {
        return true;
    }
    if o4.abs() < 1e-12 && on_seg(b1, a2, b2) {
        return true;
    }
    false
}

pub fn polygons_intersect(a: &[Point], b: &[Point]) -> bool {
    for poly in [a, b] {
        let other = if poly.as_ptr() == a.as_ptr() { b } else { a };
        for p in poly {
            if point_in_polygon(p, other) {
                return true;
            }
        }
        for i in 0..poly.len() {
            let p1 = &poly[i];
            let p2 = &poly[(i + 1) % poly.len()];
            for j in 0..other.len() {
                let q1 = &other[j];
                let q2 = &other[(j + 1) % other.len()];
                if segments_intersect(p1, p2, q1, q2) {
                    return true;
                }
            }
        }
    }
    false
}

fn bbox(poly: &[Point]) -> (f64, f64, f64, f64) {
    let mut min_x = f64::INFINITY;
    let mut min_y = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    for p in poly {
        min_x = min_x.min(p.x);
        min_y = min_y.min(p.y);
        max_x = max_x.max(p.x);
        max_y = max_y.max(p.y);
    }
    (min_x, min_y, max_x, max_y)
}

pub fn overlap_ratio(zone: &[Point], fire: &[Point]) -> f64 {
    if !polygons_intersect(zone, fire) {
        return 0.0;
    }
    let (zx0, zy0, zx1, zy1) = bbox(zone);
    let zi = (zx1 - zx0) * (zy1 - zy0);
    if zi <= 0.0 {
        return 0.0;
    }
    let (fx0, fy0, fx1, fy1) = bbox(fire);
    let ix = (zx1.min(fx1) - zx0.max(fx0)).max(0.0);
    let iy = (zy1.min(fy1) - zy0.max(fy0)).max(0.0);
    (ix * iy / zi).min(1.0)
}

pub fn centroid(poly: &[Point]) -> Point {
    let n = poly.len().max(1) as f64;
    let sx: f64 = poly.iter().map(|p| p.x).sum();
    let sy: f64 = poly.iter().map(|p| p.y).sum();
    Point { x: sx / n, y: sy / n }
}
