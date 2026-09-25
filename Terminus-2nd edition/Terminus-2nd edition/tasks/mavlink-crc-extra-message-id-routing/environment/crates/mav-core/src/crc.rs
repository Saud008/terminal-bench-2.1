pub fn crc_accumulate(data: u8, crc: u16) -> u16 {
    let mut tmp = (data as u16) ^ (crc & 0xFF);
    tmp ^= (tmp << 4) & 0xFF;
    ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
}

pub fn crc_v2(header_and_payload: &[u8], crc_extra: u8) -> u16 {
    let mut crc = 0xFFFF_u16;
    for &b in header_and_payload {
        crc = crc_accumulate(b, crc);
    }
    crc = crc_accumulate(crc_extra, crc);
    crc
}
