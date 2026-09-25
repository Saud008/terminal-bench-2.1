use crate::maritime_types::AisRow;

pub fn arrange_points(points: &mut [AisRow]) {
    points.sort_by_key(|p| (p.lat * 1_000_000.0) as i64);
}
