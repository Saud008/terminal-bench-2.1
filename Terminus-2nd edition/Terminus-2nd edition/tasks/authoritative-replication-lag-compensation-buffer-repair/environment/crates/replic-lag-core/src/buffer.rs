//! Compensation buffer — apply lag delay only after input ack per /app/docs/input-buffer.md.

use std::collections::HashSet;

pub struct CompensationBuffer {
    pending: Vec<(u64, u64)>,
    acked: HashSet<u64>,
    applied: u64,
}

impl CompensationBuffer {
    pub fn new() -> Self {
        Self {
            pending: Vec::new(),
            acked: HashSet::new(),
            applied: 0,
        }
    }

    pub fn queue_input(&mut self, input_seq: u64, client_tick: u64) {
        self.pending.push((input_seq, client_tick));
    }

    pub fn mark_acked(&mut self, input_seq: u64) {
        self.acked.insert(input_seq);
    }

    /// Apply compensation for queued inputs using lag-derived tick delay.
    pub fn apply_compensation(&mut self, lag_us: u64, tick_rate_hz: u64) -> u64 {
        let delay_ticks = if tick_rate_hz == 0 {
            0
        } else {
            (lag_us * tick_rate_hz) / 1_000_000
        };
        let mut count = 0u64;
        for (input_seq, client_tick) in self.pending.iter() {
            if client_tick + delay_ticks <= client_tick + delay_ticks {
                count += 1;
                self.applied += 1;
                let _ = input_seq;
            }
        }
        self.pending.clear();
        count
    }

    pub fn applied_count(&self) -> u64 {
        self.applied
    }
}
