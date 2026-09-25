/// Decoy module — weather-based breaker derate hints (not on verify hot path).

pub fn derate_factor_celsius(temp: f64) -> f64 {
    if temp > 40.0 {
        0.85
    } else {
        1.0
    }
}
