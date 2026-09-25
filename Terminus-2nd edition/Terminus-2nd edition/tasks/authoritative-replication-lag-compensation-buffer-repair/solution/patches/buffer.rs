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

    pub fn apply_compensation(&mut self, lag_us: u64, tick_rate_hz: u64) -> u64 {
        let delay_ticks = if tick_rate_hz == 0 {
            0
        } else {
            (lag_us * tick_rate_hz) / 1_000_000
        };
        let mut count = 0u64;
        let mut counted = HashSet::new();
        let mut remaining = Vec::new();
        for (input_seq, client_tick) in self.pending.drain(..) {
            if self.acked.contains(&input_seq) {
                if !counted.contains(&input_seq) && client_tick + delay_ticks >= client_tick {
                    counted.insert(input_seq);
                    count += 1;
                    self.applied += 1;
                }
            } else {
                remaining.push((input_seq, client_tick));
            }
        }
        self.pending = remaining;
        count
    }

    pub fn applied_count(&self) -> u64 {
        self.applied
    }
}
