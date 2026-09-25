use crate::model::Q16;

pub const Q16_SCALE: f64 = 65536.0;

pub fn edge_weight(cost_q16: Q16) -> f64 {
    cost_q16 as f64 / Q16_SCALE
}

pub fn path_total_q16(edge_costs_f64: &[f64]) -> Q16 {
    let mut acc: i64 = 0;
    for cost in edge_costs_f64 {
        acc += (cost * Q16_SCALE).round() as i64;
    }
    acc as Q16
}

pub fn combine_q16_manifest(cost_q16: Q16) -> Q16 {
    cost_q16
}
