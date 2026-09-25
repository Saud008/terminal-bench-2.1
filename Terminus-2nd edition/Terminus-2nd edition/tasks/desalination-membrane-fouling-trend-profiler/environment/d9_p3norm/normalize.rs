pub fn compute_ndp(
    pressure: f64,
    p_base: f64,
    temperature: f64,
    t_ref: f64,
    flow: f64,
    q_ref: f64,
    alpha: f64,
    beta: f64,
    salinity: f64,
) -> f64 {
    let dp = pressure - p_base;
    let temp_factor = (temperature / t_ref).powf(alpha);
    let flow_factor = (q_ref / flow).powf(beta);
    let brine = 1.0 + salinity / 1000.0;
    dp * temp_factor * flow_factor * brine
}
