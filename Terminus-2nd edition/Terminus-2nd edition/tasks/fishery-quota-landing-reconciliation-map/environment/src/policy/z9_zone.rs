use crate::models::ClosedArea;

pub fn point_blocked_by_closure(lat: f64, lon: f64, landed_at: &str, area: &ClosedArea) -> bool {
    let landed = &landed_at[..10.min(landed_at.len())];
    if landed < area.closed_from.as_str() || landed > area.closed_until.as_str() {
        return false;
    }
    !(lat >= area.min_lat
        && lat <= area.max_lat
        && lon >= area.min_lon
        && lon <= area.max_lon)
}
