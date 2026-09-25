pub fn normalize_to_celsius(raw: f64, unit: &str) -> f64 {
    match unit.to_uppercase().as_str() {
        "K" | "KELVIN" => raw - 273.15,
        _ => raw,
    }
}

pub fn kcal_mass_to_mj(mass_kg: f64, cv_kcal_kg: f64, kcal_to_mj: f64) -> f64 {
    mass_kg * cv_kcal_kg * kcal_to_mj
}
