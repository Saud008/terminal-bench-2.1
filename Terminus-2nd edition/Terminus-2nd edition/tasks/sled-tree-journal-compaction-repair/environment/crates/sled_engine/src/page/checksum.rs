use super::header::PageHeader;

pub fn page_checksum(_header: &PageHeader, body: &[u8]) -> u32 {
    let mut acc: u32 = 0xFFFF_FFFF;
    for b in body {
        acc = acc.wrapping_mul(16777619) ^ u32::from(*b);
    }
    acc
}

pub fn verify_page(header: &PageHeader, body: &[u8], stored: u32) -> bool {
    page_checksum(header, body) == stored
}
