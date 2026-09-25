use crate::models::TiltScan;

pub fn sort_tilts_by_elevation(tilts: &mut [TiltScan]) {
    tilts.sort_by(|a, b| {
        a.elevation_deg
            .partial_cmp(&b.elevation_deg)
            .unwrap_or(std::cmp::Equal)
    });
}
