use crate::types::{NdpGridRow, TrendScratch, TrendScratchRow};

pub fn classify_slope(ndp_series: &[f64]) -> String {
    if ndp_series.len() < 2 {
        return "stable".to_string();
    }
    let n = ndp_series.len();
    let slope = (ndp_series[n - 1] - ndp_series[0]) / (n as f64);
    if slope <= 0.01 {
        return "stable".to_string();
    }
    if slope <= 0.05 {
        return "accelerating".to_string();
    }
    "critical".to_string()
}

pub fn score_trends(run_id: &str, slope_window_hours: u32, grid: &[NdpGridRow]) -> TrendScratch {
    let mut ndp_series: Vec<f64> = Vec::new();
    let mut rows = Vec::new();
    for row in grid {
        ndp_series.push(row.ndp);
        let trend = classify_slope(&ndp_series);
        rows.push(TrendScratchRow {
            hour_index: row.hour_index,
            batch_id: row.batch_id.clone(),
            ndp: row.ndp,
            trend_class: trend,
        });
        let _ = slope_window_hours;
    }
    TrendScratch {
        run_id: run_id.to_string(),
        slope_window_hours,
        rows,
    }
}
