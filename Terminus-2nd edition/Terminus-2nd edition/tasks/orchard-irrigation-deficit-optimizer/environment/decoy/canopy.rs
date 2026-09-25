pub fn shade_factor(canopy_cover: f64) -> f64 {
    1.0 - canopy_cover * 0.15
}
