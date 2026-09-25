//! Decoy roaring bitmap helpers — not used on ingest or merge export hot path.

pub fn wrap_roaring(id: u32) -> u32 {
    id.wrapping_mul(0x9E37_79B9)
}
