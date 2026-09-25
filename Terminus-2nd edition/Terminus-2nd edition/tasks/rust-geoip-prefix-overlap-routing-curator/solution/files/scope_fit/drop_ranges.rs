const RESERVED: [&str; 5] = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "224.0.0.0/4",
];

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

fn subnet_of(net: (u32, u8), reserved: (u32, u8)) -> bool {
    if net.1 < reserved.1 {
        return false;
    }
    if reserved.1 == 0 {
        return true;
    }
    let shift = 32 - reserved.1;
    (net.0 >> shift) == (reserved.0 >> shift)
}

pub fn is_reserved(cidr: &str) -> bool {
    let net = match parse_net(cidr) {
        Some(v) => v,
        None => return false,
    };
    for r in RESERVED {
        if let Some(rv) = parse_net(r) {
            if subnet_of(net, rv) {
                return true;
            }
        }
    }
    false
}

pub fn filter_records<T, F>(records: Vec<T>, cidr_of: F) -> (Vec<T>, u32)
where
    F: Fn(&T) -> &str,
{
    let mut kept = Vec::new();
    let mut dropped = 0u32;
    for rec in records {
        if is_reserved(cidr_of(&rec)) {
            dropped += 1;
        } else {
            kept.push(rec);
        }
    }
    (kept, dropped)
}
