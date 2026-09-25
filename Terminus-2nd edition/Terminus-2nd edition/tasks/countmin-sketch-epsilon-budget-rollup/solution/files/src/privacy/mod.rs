use crate::types::EpsilonLineage;

pub fn compose_epsilons(values: Vec<f64>) -> EpsilonLineage {
    let sum_sq: f64 = values.iter().map(|v| v * v).sum();
    let composed = sum_sq.sqrt();
    EpsilonLineage {
        raw_epsilons: values,
        composed_epsilon: composed,
    }
}
