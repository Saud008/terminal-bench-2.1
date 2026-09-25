use crate::types::StagedRecord;

/// STUB — lexicographically smaller feed_id wins per /app/docs/duplicate-prefix-precedence.md
pub fn pick_winner<'a>(_a: &'a StagedRecord, _b: &'a StagedRecord) -> &'a StagedRecord {
    unimplemented!("STUB: pick_winner — see /app/docs/duplicate-prefix-precedence.md")
}

/// STUB — one winner per normalized prefix key via pick_winner.
pub fn resolve_records(_records: &[StagedRecord]) -> Vec<StagedRecord> {
    unimplemented!("STUB: resolve_records — see /app/docs/duplicate-prefix-precedence.md")
}
