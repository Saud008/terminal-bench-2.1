use crate::geo_fence;
use crate::catalog_schema::{ExclusionZone, TransmitterSite};

pub fn site_excluded(site: &TransmitterSite, exclusions: &[ExclusionZone]) -> bool {
    for ex in exclusions {
        if ex.band_id != site.band_id {
            continue;
        }
        if geo_fence::point_in_bbox(site.lat, site.lon, &ex.area) {
            return true;
        }
    }
    false
}
