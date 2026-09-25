//! EWMA lag estimator — contract in /app/docs/lag-estimator.md.

/// Smoothing factor for EWMA lag estimate (not a simple mean).
pub const EWMA_ALPHA: f64 = 0.25;

pub struct LagEstimator {
    samples: Vec<u64>,
}

impl LagEstimator {
    pub fn new() -> Self {
        Self {
            samples: Vec::new(),
        }
    }

    pub fn record_rtt_us(&mut self, rtt_us: u64) {
        self.samples.push(rtt_us);
    }

    /// Return lag estimate in microseconds.
    pub fn estimate_us(&self) -> u64 {
        if self.samples.is_empty() {
            return 0;
        }
        let sum: u64 = self.samples.iter().sum();
        sum / self.samples.len() as u64
    }

    pub fn method_name(&self) -> &'static str {
        "mean"
    }
}
