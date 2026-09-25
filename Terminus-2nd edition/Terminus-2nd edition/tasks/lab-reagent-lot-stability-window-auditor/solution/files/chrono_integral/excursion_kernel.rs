use crate::win_schema::TelemetryRow;

pub fn excursion_minutes(rows: &[TelemetryRow]) -> u32 {
    rows.iter()
        .filter(|r| r.celsius > r.threshold_celsius && r.minute_index >= r.excursion_limit_minutes)
        .map(|r| r.minute_index)
        .max()
        .unwrap_or(0)
}

pub fn severity_score(excursion_minutes: u32, celsius_peak: f64, threshold: f64) -> u32 {
    let over = (celsius_peak - threshold).max(0.0) as u32;
    excursion_minutes.saturating_mul(10).saturating_add(over)
}
