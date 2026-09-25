pub fn propagate_orbit(semi_major_km: f64, eccentricity: f64, mean_anomaly_deg: f64) -> f64 {
    semi_major_km * (1.0 + eccentricity) + mean_anomaly_deg * 0.001
}
