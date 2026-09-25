/// Block traversal helpers.

pub fn body_len(block_total_length: u32) -> usize {
    if block_total_length < 12 {
        return 0;
    }
    block_total_length as usize - 12
}

/// Advance offset after consuming a block.
pub fn next_block_offset(current: usize, block_total_length: u32, body_len: usize) -> usize {
    let pad = (4 - (body_len % 4)) % 4;
    current + 8 + body_len + pad
}
