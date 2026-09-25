use std::collections::HashMap;

pub fn apply_drift(
    normalized: &HashMap<String, Vec<f64>>,
    factors: &HashMap<String, f64>,
) -> HashMap<String, Vec<f64>> {
    let mut out = HashMap::new();
    for (qubit, probs) in normalized {
        let factor = factors.get(qubit).copied().unwrap_or(1.0);
        let adjusted: Vec<f64> = probs
            .iter()
            .map(|p| p + (factor - 1.0))
            .map(|v| v.max(0.0))
            .collect();
        let sum: f64 = adjusted.iter().sum();
        let renorm: Vec<f64> = if sum > 0.0 {
            adjusted.iter().map(|v| v / sum).collect()
        } else {
            adjusted
        };
        out.insert(qubit.clone(), renorm);
    }
    out
}
