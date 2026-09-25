fn parse_net(cidr: &str) -> Option<(u32, u8)> {
    let parts: Vec<&str> = cidr.split('/').collect();
    if parts.len() != 2 {
        return None;
    }
    let prefix: u8 = parts[1].parse().ok()?;
    let octets: Vec<u8> = parts[0].split('.').filter_map(|o| o.parse().ok()).collect();
    if octets.len() != 4 {
        return None;
    }
    let addr = u32::from(octets[0]) << 24
        | u32::from(octets[1]) << 16
        | u32::from(octets[2]) << 8
        | u32::from(octets[3]);
    Some((addr, prefix))
}

pub fn contains(outer: &str, inner: &str) -> bool {
    let (o_addr, o_pref) = match parse_net(outer) {
        Some(v) => v,
        None => return false,
    };
    let (i_addr, i_pref) = match parse_net(inner) {
        Some(v) => v,
        None => return false,
    };
    if i_pref < o_pref {
        return false;
    }
    if o_pref == 0 {
        return o_addr != i_addr || o_pref != i_pref;
    }
    let shift = 32 - o_pref;
    (o_addr >> shift) == (i_addr >> shift) && outer != inner
}
