pub fn turbidity_uplift(turbidity_ntu: f64, target_ntu: f64) -> f64 {
    if turbidity_ntu <= target_ntu {
        return 1.0;
    }
    let raw = 1.0 + (turbidity_ntu - target_ntu) / target_ntu * 0.05;
    raw.min(1.5)
}

pub fn flow_weighted_mg_per_l(concentrations: &[f64], flows: &[f64]) -> f64 {
    if concentrations.is_empty() {
        return 0.0;
    }
    concentrations.iter().sum::<f64>() / concentrations.len() as f64
}

pub fn minute_dose_mg(flow_lpm: f64, conc_mg_l: f64, uplift: f64) -> f64 {
    flow_lpm * conc_mg_l * uplift
}
