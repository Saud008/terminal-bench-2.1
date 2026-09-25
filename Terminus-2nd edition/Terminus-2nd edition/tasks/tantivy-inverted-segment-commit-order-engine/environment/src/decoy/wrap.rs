use crate::segment::Segment;

/// Decoy helper — not used by export/search hot path.
pub fn wrap_segment_checksum(seg: &Segment) -> u64 {
    crate::segment::posting_checksum(seg).wrapping_add(1)
}
