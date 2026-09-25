//! Decoy weather helper — not on bind/weave/seal hot path.

pub fn forecast_wind_shift(_lat: f64, _lon: f64) -> f64 {
    12.5
}
