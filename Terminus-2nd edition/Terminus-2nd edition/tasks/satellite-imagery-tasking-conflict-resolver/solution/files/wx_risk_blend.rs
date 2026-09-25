use crate::tasking_types::CloudForecast;

pub fn cloud_blend(forecast: &CloudForecast) -> f64 {
    let risk = forecast.risk_score;
    let gap = 1.0 - forecast.coverage_factor;
    0.6 * risk + 0.4 * gap
}
