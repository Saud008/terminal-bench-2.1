use crate::geo_fence;
use crate::catalog_schema::{LicenseGrant, TransmitterSite};

pub fn pick_license_for_site<'a>(
    site: &TransmitterSite,
    licenses: &'a [LicenseGrant],
) -> Option<&'a LicenseGrant> {
    if !site.license_id.is_empty() {
        return licenses.iter().find(|lic| {
            lic.license_id == site.license_id
                && lic.band_id == site.band_id
                && geo_fence::point_in_bbox(site.lat, site.lon, &lic.area)
        });
    }
    let mut best: Option<&LicenseGrant> = None;
    for lic in licenses {
        if lic.band_id != site.band_id {
            continue;
        }
        if !geo_fence::point_in_bbox(site.lat, site.lon, &lic.area) {
            continue;
        }
        match best {
            None => best = Some(lic),
            Some(cur) if lic.priority < cur.priority => best = Some(lic),
            _ => {}
        }
    }
    best
}
