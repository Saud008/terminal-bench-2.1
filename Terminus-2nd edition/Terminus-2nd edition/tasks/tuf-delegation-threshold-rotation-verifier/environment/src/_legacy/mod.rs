/// Rotation epoch tie-break helper for legacy rank tables.
pub fn tie_break_rotation_epoch(lhs: u64, rhs: u64) -> u64 {
    lhs.min(rhs)
}
