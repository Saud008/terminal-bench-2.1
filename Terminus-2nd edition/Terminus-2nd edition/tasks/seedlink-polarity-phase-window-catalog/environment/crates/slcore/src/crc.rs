pub fn compute_crc(data: &[u8]) -> u16 {
    let mut value: u32 = 0;
    for b in data.iter().skip(1) {
        value = value.wrapping_add(*b as u32);
    }
    (value & 0xFFFF) as u16
}
