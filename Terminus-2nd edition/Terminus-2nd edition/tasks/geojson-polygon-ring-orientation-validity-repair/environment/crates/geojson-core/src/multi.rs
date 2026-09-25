use crate::types::MultiPolygonCoords;

pub fn normalize_multipolygon(mut polys: MultiPolygonCoords) -> (MultiPolygonCoords, u32) {
    polys.reverse();
    (polys, 1)
}
