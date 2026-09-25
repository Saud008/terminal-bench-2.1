use crate::types::EpsilonLineage;

pub fn compose_epsilons(values: Vec<f64>) -> EpsilonLineage {
    let composed = values.iter().copied().sum();
    EpsilonLineage {
        raw_epsilons: values,
        composed_epsilon: composed,
    }
}
