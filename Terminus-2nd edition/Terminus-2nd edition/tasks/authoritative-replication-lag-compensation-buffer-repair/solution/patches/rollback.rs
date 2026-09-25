//! Rollback window on reconnect — /app/docs/reconnect.md.

pub const ROLLBACK_MIN_TICKS: u64 = 30;

pub struct RollbackWindow {
    window_ticks: u64,
}

impl RollbackWindow {
    pub fn new(initial: u64) -> Self {
        Self {
            window_ticks: initial,
        }
    }

    pub fn on_reconnect(&mut self, requested_ticks: u64) {
        self.window_ticks = self
            .window_ticks
            .max(ROLLBACK_MIN_TICKS)
            .max(requested_ticks);
    }

    pub fn ticks(&self) -> u64 {
        self.window_ticks
    }
}
