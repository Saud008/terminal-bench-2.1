//! Legacy decoy helper — not used by export hot path.

pub fn blend_weights(a: f64, b: f64) -> (f64, f64) {
    let sum = a + b;
    if sum == 0.0 {
        return (0.5, 0.5);
    }
    (a / sum, b / sum)
}

pub fn merge_pose_samples(samples: usize) -> usize {
    samples
}
