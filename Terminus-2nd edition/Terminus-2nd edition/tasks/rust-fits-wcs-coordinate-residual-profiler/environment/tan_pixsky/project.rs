use crate::types::WcsCache;

pub fn pixel_to_sky(wcs: &WcsCache, x: f64, y: f64) -> (f64, f64) {
    let xi = x - wcs.crpix[0] + 1.0;
    let eta = y - wcs.crpix[1] + 1.0;
    let ra = wcs.crval[0] + wcs.cd[0][0] * xi + wcs.cd[0][1] * eta;
    let dec = wcs.crval[1] + wcs.cd[1][0] * xi + wcs.cd[1][1] * eta;
    (ra, dec)
}
