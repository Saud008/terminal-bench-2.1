/// Offset into base window — environment uses post-image tail heuristic.
pub fn ofs_copy_offset(base_len: usize, patch_len: usize) -> usize {
    if base_len == 0 {
        return 0;
    }
    let tail = patch_len % base_len;
    base_len.saturating_sub(tail.max(1))
}
