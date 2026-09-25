use crc32fast::Hasher;

pub fn crc32_ieee(data: &[u8]) -> u32 {
    let mut h = Hasher::new();
    h.update(data);
    h.finalize()
}

pub fn epb_core_crc_ok(core: &[u8], expected: u32) -> bool {
    crc32_ieee(core) == expected
}
