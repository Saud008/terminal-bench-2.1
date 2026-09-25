pub fn normalize_cidr(raw: &str) -> Result<String, String> {
    let trimmed = raw.trim();
    let parts: Vec<&str> = trimmed.split('/').collect();
    if parts.len() != 2 {
        return Err("invalid cidr".into());
    }
    let prefix: u8 = parts[1].parse().map_err(|_| "bad prefix".to_string())?;
    if prefix > 32 {
        return Err("bad prefix".into());
    }
    let octets: Vec<u8> = parts[0]
        .split('.')
        .map(|o| o.parse().map_err(|_| "bad ip".to_string()))
        .collect::<Result<Vec<u8>, _>>()?;
    if octets.len() != 4 {
        return Err("bad ip".into());
    }
    let mut addr = u32::from(octets[0]) << 24
        | u32::from(octets[1]) << 16
        | u32::from(octets[2]) << 8
        | u32::from(octets[3]);
    if prefix < 32 {
        let mask = if prefix == 0 {
            0
        } else {
            u32::MAX << (32 - prefix)
        };
        addr &= mask;
    }
    Ok(format!(
        "{}.{}.{}.{}/{}",
        (addr >> 24) & 0xff,
        (addr >> 16) & 0xff,
        (addr >> 8) & 0xff,
        addr & 0xff,
        prefix
    ))
}
