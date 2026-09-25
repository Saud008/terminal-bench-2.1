use crate::hazard_schema::Point;

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

fn bbox_overlap(a: &[Point], b: &[Point]) -> bool {
    let (ax0, ay0, ax1, ay1) = bbox(a);
    let (bx0, by0, bx1, by1) = bbox(b);
    !(ax1 < bx0 || bx1 < ax0 || ay1 < by0 || by1 < ay0)
}

pub fn polygons_intersect(a: &[Point], b: &[Point]) -> bool {
    bbox_overlap(a, b)
}

pub fn overlap_ratio(zone: &[Point], fire: &[Point]) -> f64 {
    if !polygons_intersect(zone, fire) {
        return 0.0;
    }
    let (_, _, zw, zh) = bbox(zone);
    let (_, _, fw, fh) = bbox(fire);
    let zi = zw * zh;
    if zi <= 0.0 {
        return 0.0;
    }
    let inter_w = (zw.min(fw)).max(0.0);
    let inter_h = (zh.min(fh)).max(0.0);
    (inter_w * inter_h / zi).min(1.0)
}

pub fn centroid(poly: &[Point]) -> Point {
    let n = poly.len().max(1) as f64;
    let sx: f64 = poly.iter().map(|p| p.x).sum();
    let sy: f64 = poly.iter().map(|p| p.y).sum();
    Point { x: sx / n, y: sy / n }
}
