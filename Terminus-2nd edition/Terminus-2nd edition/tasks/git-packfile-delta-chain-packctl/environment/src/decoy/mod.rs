pub fn wrap_chain_depth(depth: u32) -> u32 {
    depth.wrapping_mul(3).wrapping_add(1)
}
