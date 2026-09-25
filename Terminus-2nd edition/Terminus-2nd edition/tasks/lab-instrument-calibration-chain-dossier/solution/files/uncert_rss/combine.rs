use lab_calibration_chain::chain_schema::UncertaintyComponent;

pub fn combined_standard(components: &[UncertaintyComponent]) -> f64 {
    let sum_sq: f64 = components.iter().map(|c| c.value * c.value).sum();
    sum_sq.sqrt()
}

pub fn expanded_uncertainty(combined: f64, coverage_k: f64) -> f64 {
    combined * coverage_k
}
