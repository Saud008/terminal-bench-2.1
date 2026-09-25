use crate::error::Result;

/// Victoreen baseline μ0(E) = a + b * E^{-3} via least squares on pre-edge points.
pub fn fit_victoreen(energies: &[f64], mus: &[f64]) -> Result<(f64, f64)> {
    assert_eq!(energies.len(), mus.len());
    let n = energies.len();
    if n == 0 {
        return Ok((0.0, 0.0));
    }
    if n == 1 {
        return Ok((mus[0], 0.0));
    }
    // Solve [1, x_i; ...] for μ = a + b*x where x = E^{-3}
    let mut sum_x = 0.0;
    let mut sum_y = 0.0;
    let mut sum_xx = 0.0;
    let mut sum_xy = 0.0;
    for (&e, &mu) in energies.iter().zip(mus.iter()) {
        let x = e.powi(-3);
        sum_x += x;
        sum_y += mu;
        sum_xx += x * x;
        sum_xy += x * mu;
    }
    let nf = n as f64;
    let denom = nf * sum_xx - sum_x * sum_x;
    if denom.abs() < 1e-18 {
        return Ok((sum_y / nf, 0.0));
    }
    let b = (nf * sum_xy - sum_x * sum_y) / denom;
    let a = (sum_y - b * sum_x) / nf;
    Ok((a, b))
}

pub fn evaluate(a: f64, b: f64, e: f64) -> f64 {
    a + b * e.powi(-3)
}

pub fn select_pre_edge<'a>(
    points: &'a [(f64, f64)],
    min_window_lo: f64,
) -> Vec<(f64, f64)> {
    let pre: Vec<(f64, f64)> = points
        .iter()
        .copied()
        .filter(|(e, _)| *e < min_window_lo)
        .collect();
    if pre.len() >= 3 {
        pre
    } else {
        pre
    }
}
