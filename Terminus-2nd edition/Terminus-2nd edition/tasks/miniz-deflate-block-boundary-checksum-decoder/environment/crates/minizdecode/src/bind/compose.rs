//! Compose helper for staging metadata — not wired into stream decode loop.

pub fn compose_block_label(index: u32, final_block: bool) -> String {
    format!("block-{index}-{}", if final_block { "final" } else { "cont" })
}
