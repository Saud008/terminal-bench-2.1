/// The parts of a request URL the cookie algorithms look at.
#[derive(Clone, Debug)]
pub struct Url {
    /// The URL exactly as written in the transcript.
    pub raw: String,
    /// `https` (a secure protocol in RFC 6265 terms).
    pub secure: bool,
    /// Canonicalized (lower case) host, port removed.
    pub host: String,
    /// Path without query or fragment; `/` when the URL has none.
    pub path: String,
}

impl Url {
    pub fn parse(raw: &str) -> Result<Url, String> {
        let lower = raw.to_ascii_lowercase();
        let (secure, rest) = if lower.starts_with("https://") {
            (true, &raw[8..])
        } else if lower.starts_with("http://") {
            (false, &raw[7..])
        } else {
            return Err(format!("unsupported URL {raw:?}"));
        };

        let end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
        let authority = &rest[..end];
        if authority.contains('@') || authority.starts_with('[') {
            return Err(format!("unsupported authority in {raw:?}"));
        }
        let host = match authority.rsplit_once(':') {
            Some((h, port)) if !port.is_empty() && port.bytes().all(|b| b.is_ascii_digit()) => h,
            Some(_) => return Err(format!("bad port in {raw:?}")),
            None => authority,
        };
        if host.is_empty() {
            return Err(format!("missing host in {raw:?}"));
        }

        let tail = &rest[end..];
        let path_end = tail.find(['?', '#']).unwrap_or(tail.len());
        let path = match &tail[..path_end] {
            "" => "/".to_string(),
            p => p.to_string(),
        };

        Ok(Url {
            raw: raw.to_string(),
            secure,
            host: host.to_ascii_lowercase(),
            path,
        })
    }
}
