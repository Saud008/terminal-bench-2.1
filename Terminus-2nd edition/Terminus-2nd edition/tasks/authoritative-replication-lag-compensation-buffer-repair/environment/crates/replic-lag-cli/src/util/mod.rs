//! Unused CLI-side decoy — agents must not wire this into ingest/simulate/export.

pub fn ignore_tick_hint(_hz: u64) -> u64 {
    60
}
