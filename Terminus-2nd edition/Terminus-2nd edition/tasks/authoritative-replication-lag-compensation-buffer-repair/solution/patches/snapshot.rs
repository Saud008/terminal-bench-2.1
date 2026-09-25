//! Snapshot delta merge with gap fill — /app/docs/snapshot-merge.md.

use crate::model::SnapshotRow;

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

    pub fn set_gap_fills(&mut self, count: u64) {
        self.gap_fills = count;
    }

    pub fn merge_rows(&mut self) -> Vec<SnapshotRow> {
        if self.deltas.is_empty() {
            return Vec::new();
        }
        let min_seq = self.deltas.iter().map(|(s, _, _)| *s).min().unwrap();
        let max_seq = self.deltas.iter().map(|(s, _, _)| *s).max().unwrap();
        let mut xor_by_seq: std::collections::BTreeMap<u64, u64> = std::collections::BTreeMap::new();
        for (seq, _, xor) in &self.deltas {
            xor_by_seq.insert(*seq, *xor);
        }

        let mut rows = Vec::new();
        let mut cumulative = 0u64;
        for seq in min_seq..=max_seq {
            if let Some(xor) = xor_by_seq.get(&seq) {
                cumulative ^= *xor;
            }
            rows.push(SnapshotRow {
                seq,
                state_hash: cumulative,
            });
        }
        rows
    }

    pub fn merged_state_hash(&self) -> u64 {
        if self.deltas.is_empty() {
            return 0;
        }
        let min_seq = self.deltas.iter().map(|(s, _, _)| *s).min().unwrap();
        let max_seq = self.deltas.iter().map(|(s, _, _)| *s).max().unwrap();
        let mut xor_by_seq: std::collections::BTreeMap<u64, u64> = std::collections::BTreeMap::new();
        for (seq, _, xor) in &self.deltas {
            xor_by_seq.insert(*seq, *xor);
        }
        let mut cumulative = 0u64;
        for seq in min_seq..=max_seq {
            if let Some(xor) = xor_by_seq.get(&seq) {
                cumulative ^= *xor;
            }
        }
        cumulative
    }

    pub fn gap_fills(&self) -> u64 {
        self.gap_fills
    }
}
