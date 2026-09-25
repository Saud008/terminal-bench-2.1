pub fn turbidity_uplift(turbidity_ntu: f64, target_ntu: f64) -> f64 {
    if turbidity_ntu <= target_ntu {
        return 1.0;
    }
    let raw = 1.0 + (turbidity_ntu - target_ntu) / target_ntu * 0.10;
    raw.min(1.5)
}

pub fn flow_weighted_mg_per_l(concentrations: &[f64], flows: &[f64]) -> f64 {
    if concentrations.is_empty() {
        return 0.0;
    }
    let mut num = 0.0;
    let mut den = 0.0;
    for (c, f) in concentrations.iter().zip(flows.iter()) {
        num += c * f;
        den += f;
    }
    if den <= 0.0 {
        0.0
    } else {
        num / den
    }
}

pub fn minute_dose_mg(flow_lpm: f64, conc_mg_l: f64, uplift: f64) -> f64 {
    flow_lpm * conc_mg_l * uplift
}
