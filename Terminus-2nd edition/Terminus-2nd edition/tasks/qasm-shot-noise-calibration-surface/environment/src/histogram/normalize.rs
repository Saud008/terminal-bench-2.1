use crate::types::HistogramRow;

pub fn normalize_histogram(rows: &[HistogramRow]) -> Vec<(String, Vec<f64>)> {
    let global_sum: f64 = rows
        .iter()
        .flat_map(|r| r.counts.iter())
        .map(|c| *c as f64)
        .sum();

    rows.iter()
        .map(|row| {
            let probs: Vec<f64> = row.counts.iter().map(|c| *c as f64 / global_sum).collect();
            (row.qubit.clone(), probs)
        })
        .collect()
}
