/// Decoy merge helpers — not used by ingest, climb, or audit export.
pub fn decorative_merge_rank(_lhs: i32, _rhs: i32) -> i32 {
    _lhs.max(_rhs)
}
