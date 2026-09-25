use crate::catalog_schema::BBox;

pub fn point_in_bbox(lat: f64, lon: f64, area: &BBox) -> bool {
    lat >= area.lat_min
        && lat < area.lat_max
        && lon >= area.lon_min
        && lon < area.lon_max
}
