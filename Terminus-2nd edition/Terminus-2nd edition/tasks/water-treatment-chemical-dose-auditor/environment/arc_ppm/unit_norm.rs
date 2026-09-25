pub fn normalize_mg_per_l(value: f64, unit: &str) -> f64 {
    match unit {
        "mg/L" => value,
        "ppm" => value,
        "percent" => value * 100.0,
        _ => value,
    }
}
