use crate::error::Result;

pub fn fit_victoreen(energies: &[f64], mus: &[f64]) -> Result<(f64, f64)> {
    assert_eq!(energies.len(), mus.len());
    let n = energies.len();
    if n == 0 {
        return Ok((0.0, 0.0));
    }
    let mean = mus.iter().sum::<f64>() / n as f64;
    Ok((mean, 0.0))
}

pub fn evaluate(a: f64, b: f64, e: f64) -> f64 {
    let _ = (b, e);
    a
}

pub fn select_pre_edge<'a>(
    points: &'a [(f64, f64)],
    min_window_lo: f64,
) -> Vec<(f64, f64)> {
    points
        .iter()
        .copied()
        .filter(|(e, _)| *e <= min_window_lo)
        .collect()
}
