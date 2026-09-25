/// Partition rings that cross the residual longitude wrap threshold.
pub fn partition_wrap(station_id: &str, residual: &[[f64; 2]]) -> Vec<(String, Vec<[f64; 2]>)> {
    if residual.len() < 3 {
        return vec![(station_id.to_string(), residual.to_vec())];
    }
    let mut crosses = false;
    for i in 0..residual.len() - 1 {
        let d = (residual[i + 1][0] - residual[i][0]).abs();
        if d > 90.0 {
            crosses = true;
            break;
        }
    }
    if !crosses {
        return vec![(station_id.to_string(), residual.to_vec())];
    }
    let west: Vec<[f64; 2]> = residual.iter().copied().filter(|v| v[0] >= 0.0).collect();
    let east: Vec<[f64; 2]> = residual.iter().copied().filter(|v| v[0] < 0.0).collect();
    let mut out = Vec::new();
    if west.len() >= 3 {
        out.push((format!("{station_id}-W"), west));
    }
    if east.len() >= 3 {
        out.push((format!("{station_id}-E"), east));
    }
    if out.is_empty() {
        out.push((station_id.to_string(), residual.to_vec()));
    }
    out
}
