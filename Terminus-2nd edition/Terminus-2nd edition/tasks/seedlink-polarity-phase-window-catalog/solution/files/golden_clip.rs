pub fn clip_bit(mask: &[u8], idx: usize) -> bool {
    let byte = idx / 8;
    let bit = idx % 8;
    if byte >= mask.len() {
        return false;
    }
    ((mask[byte] >> bit) & 1) == 1
}
