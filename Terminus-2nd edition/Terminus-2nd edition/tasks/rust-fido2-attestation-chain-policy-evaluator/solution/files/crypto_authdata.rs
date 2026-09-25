pub fn parse_auth_data(bytes: &[u8]) -> Result<(bool, u32, [u8; 16]), String> {
    if bytes.len() < 37 {
        return Err("authData too short".into());
    }
    let flags = bytes[32];
    let sign_count = u32::from_be_bytes(bytes[33..37].try_into().map_err(|_| "sign_count")?);
    let uv = (flags & 0x04) != 0;
    if bytes.len() < 53 {
        return Ok((uv, sign_count, [0u8; 16]));
    }
    let mut aaguid = [0u8; 16];
    aaguid.copy_from_slice(&bytes[37..53]);
    Ok((uv, sign_count, aaguid))
}

pub fn aaguid_to_string(raw: [u8; 16]) -> String {
    format!(
        "{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}",
        raw[0], raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7],
        raw[8], raw[9], raw[10], raw[11], raw[12], raw[13], raw[14], raw[15]
    ).to_lowercase()
}
