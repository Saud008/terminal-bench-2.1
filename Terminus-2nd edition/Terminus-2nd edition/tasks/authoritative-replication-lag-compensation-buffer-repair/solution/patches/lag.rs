//! EWMA lag estimator — contract in /app/docs/lag-estimator.md.

pub const EWMA_ALPHA: f64 = 0.25;

pub struct LagEstimator {
    estimate: f64,
    initialized: bool,
}

impl LagEstimator {
    pub fn new() -> Self {
        Self {
            estimate: 0.0,
            initialized: false,
        }
    }

    pub fn record_rtt_us(&mut self, rtt_us: u64) {
        let sample = rtt_us as f64;
        if !self.initialized {
            self.estimate = sample;
            self.initialized = true;
        } else {
            self.estimate = EWMA_ALPHA * sample + (1.0 - EWMA_ALPHA) * self.estimate;
        }
    }

    pub fn estimate_us(&self) -> u64 {
        if !self.initialized {
            return 0;
        }
        self.estimate.round() as u64
    }

    pub fn method_name(&self) -> &'static str {
        "ewma"
    }
}
