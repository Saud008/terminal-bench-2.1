pub fn vwc_to_mm(vwc: f64, target_vwc: f64, root_depth_cm: f64) -> f64 {
    (target_vwc - vwc) * root_depth_cm * 10.0
}

pub fn liters_from_mm(mm: f64, area_ha: f64) -> f64 {
    mm * area_ha * 10.0
}
