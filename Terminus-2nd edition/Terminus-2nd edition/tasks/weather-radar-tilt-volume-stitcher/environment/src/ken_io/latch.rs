use crate::models::TiltScan;

pub fn sort_tilts_by_elevation(tilts: &mut [TiltScan]) {
    tilts.sort_by(|a, b| a.scan_id.cmp(&b.scan_id));
}
