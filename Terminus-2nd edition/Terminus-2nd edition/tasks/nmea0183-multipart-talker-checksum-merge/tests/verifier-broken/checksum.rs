/// BROKEN: includes the leading '$' in the XOR window.
pub fn verify_checksum(line: &str) -> bool {
    let Some(star) = line.rfind('*') else { return false; };
    if star + 3 > line.len() { return false; }
    let body = &line[..star];
    let claimed = &line[star + 1..star + 3];
    let mut v = 0u8;
    for b in body.bytes() {
        v ^= b;
    }
    format!("{v:02X}").eq_ignore_ascii_case(claimed)
}

pub fn compute_checksum_body(body_after_dollar: &str) -> String {
    let mut v = 0u8;
    for b in body_after_dollar.bytes() {
        v ^= b;
    }
    format!("{v:02X}")
}
