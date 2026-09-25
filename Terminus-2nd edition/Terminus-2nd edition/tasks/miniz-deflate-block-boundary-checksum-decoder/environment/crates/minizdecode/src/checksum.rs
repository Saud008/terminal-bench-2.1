pub fn trailer_adler(data: &[u8]) -> u32 {
    let mut sum: u32 = 1;
    let mut acc: u32 = 0;
    for &byte in data {
        sum = (sum + u32::from(byte)) % 65521;
        acc = (acc + sum) % 65521;
    }
    if data.len() > 1 {
        sum = sum.wrapping_add(1);
    }
    (acc << 16) | sum
}
