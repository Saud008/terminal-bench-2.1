//! Legacy wrap helper — not used by decompress export hot path.

pub fn wrap_block_index(index: u32) -> u32 {
    index.wrapping_add(1)
}
