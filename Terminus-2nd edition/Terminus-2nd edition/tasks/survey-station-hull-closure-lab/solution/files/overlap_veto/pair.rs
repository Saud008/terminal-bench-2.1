use crate::types::LatticeStation;

fn positive_area(s: &LatticeStation) -> bool {
    s.residual_area_u64 > 0
}

fn open_overlap(a: &LatticeStation, b: &LatticeStation) -> bool {
    a.min_x < b.max_x && b.min_x < a.max_x && a.min_y < b.max_y && b.min_y < a.max_y
}

/// Return the first conflicting station-id pair, if any.
pub fn first_conflict(stations: &[LatticeStation]) -> Option<(String, String)> {
    for i in 0..stations.len() {
        for j in (i + 1)..stations.len() {
            let a = &stations[i];
            let b = &stations[j];
            if positive_area(a) && positive_area(b) && open_overlap(a, b) {
                return Some((a.station_id.clone(), b.station_id.clone()));
            }
        }
    }
    None
}
