pub fn deficit_mm(moisture_gap_mm: f64, et_demand_mm: f64) -> f64 {
    let _ = et_demand_mm;
    moisture_gap_mm.max(0.0)
}

pub fn et_demand_mm(kc: f64, et_forecast: f64) -> f64 {
    kc * et_forecast
}
