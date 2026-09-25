//! Decoy merge helper — kept off ingest/staging/export hot path.

pub fn merge_stored_checksum(left: u16, right: u16) -> u16 {
    left.wrapping_add(right)
}
