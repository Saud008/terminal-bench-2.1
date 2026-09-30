/// True for a dotted-quad IPv4 address such as `192.0.2.7`.
pub fn is_ip_address(host: &str) -> bool {
    let parts: Vec<&str> = host.split('.').collect();
    parts.len() == 4
        && parts.iter().all(|p| {
            !p.is_empty()
                && p.len() <= 3
                && p.bytes().all(|b| b.is_ascii_digit())
                && p.parse::<u16>().map_or(false, |v| v <= 255)
        })
}

/// Domain matching (RFC 6265 section 5.1.3). Both arguments must already be
/// canonicalized.
pub fn domain_match(string: &str, domain: &str) -> bool {
    if string == domain {
        return true;
    }
    string.len() > domain.len()
        && string.ends_with(domain)
        && string.as_bytes()[string.len() - domain.len() - 1] == b'.'
}
