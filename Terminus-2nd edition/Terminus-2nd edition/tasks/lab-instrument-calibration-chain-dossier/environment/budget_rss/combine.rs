use crate::chain_schema::UncertaintyComponent;

pub fn combined_standard(components: &[UncertaintyComponent]) -> f64 {
    components.iter().map(|c| c.value).sum()
}

pub fn expanded_uncertainty(combined: f64, coverage_k: f64) -> f64 {
    combined * coverage_k
}
