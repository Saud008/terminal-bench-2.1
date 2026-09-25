use crate::types::HistogramRow;

pub fn normalize_histogram(rows: &[HistogramRow]) -> Vec<(String, Vec<f64>)> {
    rows.iter()
        .map(|row| {
            let row_sum: f64 = row.counts.iter().map(|c| *c as f64).sum();
            let probs: Vec<f64> = row.counts.iter().map(|c| *c as f64 / row_sum).collect();
            (row.qubit.clone(), probs)
        })
        .collect()
}
