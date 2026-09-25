use crate::model::Q16;

pub fn edge_weight(cost_q16: Q16) -> f64 {
    cost_q16 as f64 / 65536.0
}

pub fn path_total_q16(edge_costs_f64: &[f64]) -> Q16 {
    edge_costs_f64.iter().sum::<f64>() as Q16
}

pub fn combine_q16_manifest(cost_q16: Q16) -> f64 {
    edge_weight(cost_q16)
}
