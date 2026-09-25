//! Input ledger idempotency — /app/docs/input-ledger.md.

use std::collections::HashSet;

pub struct InputLedger {
    seen: HashSet<u64>,
    inserted: u64,
    skipped_duplicates: u64,
}

impl InputLedger {
    pub fn new() -> Self {
        Self {
            seen: HashSet::new(),
            inserted: 0,
            skipped_duplicates: 0,
        }
    }

    pub fn record_input(&mut self, input_seq: u64) -> bool {
        if self.seen.contains(&input_seq) {
            self.skipped_duplicates += 1;
            return false;
        }
        self.seen.insert(input_seq);
        self.inserted += 1;
        true
    }

    pub fn inserted_count(&self) -> u64 {
        self.inserted
    }

    pub fn skipped_duplicates(&self) -> u64 {
        self.skipped_duplicates
    }
}
