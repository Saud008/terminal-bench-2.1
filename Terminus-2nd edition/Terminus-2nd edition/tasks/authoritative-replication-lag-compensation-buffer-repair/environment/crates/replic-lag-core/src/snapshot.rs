//! Snapshot delta merge with gap fill — /app/docs/snapshot-merge.md.

use crate::model::SnapshotRow;

/// Neutral state hash used when filling missing snapshot sequence slots.
pub const GAP_FILL_HASH: u64 = 0;

pub struct SnapshotMerger {
    deltas: Vec<(u64, u64, u64)>,
    gap_fills: u64,
}

impl SnapshotMerger {
    pub fn new() -> Self {
        Self {
            deltas: Vec::new(),
            gap_fills: 0,
        }
    }

    pub fn push_delta(&mut self, snapshot_seq: u64, base_seq: u64, state_xor: u64) {
        self.deltas.push((snapshot_seq, base_seq, state_xor));
    }

    pub fn record_gap(&mut self, _expected_seq: u64) {
        self.gap_fills += 1;
    }

    /// Merge deltas into ordered snapshot rows.
    pub fn merge_rows(&mut self) -> Vec<SnapshotRow> {
        self.deltas.sort_by_key(|(seq, _, _)| *seq);
        let mut merged_state = 0u64;
        let mut rows = Vec::new();
        for (seq, _, xor) in &self.deltas {
            merged_state ^= *xor;
            rows.push(SnapshotRow {
                seq: *seq,
                state_hash: merged_state,
            });
        }
        rows
    }

    pub fn merged_state_hash(&self) -> u64 {
        let mut h = 0u64;
        for (_, _, xor) in &self.deltas {
            h ^= *xor;
        }
        h
    }

    pub fn set_gap_fills(&mut self, count: u64) {
        self.gap_fills = count;
    }

    pub fn gap_fills(&self) -> u64 {
        self.gap_fills
    }
}
