pub fn canonical_url(raw: &str) -> String {
    let (scheme, rest) = match raw.split_once("://") {
        Some((s, r)) => (s.to_lowercase(), r),
        None => ("http".to_string(), raw),
    };
    let (host_port, path_query) = match rest.split_once('/') {
        Some((h, p)) => (h, format!("/{p}")),
        None => (rest, "/".to_string()),
    };
    let mut host = host_port.split(':').next().unwrap_or(host_port).to_lowercase();
    if host_port.contains(':') {
        let port = host_port.rsplit(':').next().unwrap_or("");
        if (scheme == "http" && port == "80") || (scheme == "https" && port == "443") {
            // strip default port already handled by taking host before port
        } else if host_port.contains(':') {
            host = host_port.to_lowercase();
            if scheme == "http" && host.ends_with(":80") {
                host.truncate(host.len() - 3);
            }
            if scheme == "https" && host.ends_with(":443") {
                host.truncate(host.len() - 4);
            }
        }
    }
    let mut path = path_query;
    if path.is_empty() {
        path = "/".to_string();
    }
    path = decode_path_segments(&path);
    path = path.to_ascii_lowercase();
    let (path_only, query) = match path.split_once('?') {
        Some((p, q)) => {
            let mut parts: Vec<&str> = q.split('&').collect();
            parts.sort();
            (p.to_string(), Some(parts.join("&")))
        }
        None => (path, None),
    };
    let mut out = format!("{scheme}://{host}{path_only}");
    if let Some(q) = query {
        if !q.is_empty() {
            out.push('?');
            out.push_str(&q);
        }
    }
    out
}

fn decode_path_segments(path: &str) -> String {
    let (path_part, query) = match path.split_once('?') {
        Some((p, q)) => (p, Some(q)),
        None => (path, None),
    };
    let mut out = String::new();
    for seg in path_part.split('/') {
        if seg.is_empty() {
            out.push('/');
            continue;
        }
        if seg.contains("%2F") || seg.contains("%2f") {
            out.push_str(seg);
        } else {
            out.push_str(&percent_decode_unreserved(seg));
        }
        out.push('/');
    }
    if out.ends_with('/') && path_part != "/" {
        out.pop();
    }
    if out.is_empty() {
        out = "/".to_string();
    }
    if let Some(q) = query {
        out.push('?');
        out.push_str(q);
    }
    out
}

fn percent_decode_unreserved(seg: &str) -> String {
    let bytes = seg.as_bytes();
    let mut i = 0;
    let mut out = Vec::new();
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            let hi = hex_val(bytes[i + 1]);
            let lo = hex_val(bytes[i + 2]);
            if let (Some(h), Some(l)) = (hi, lo) {
                let ch = (h << 4) | l;
                if is_unreserved(ch) {
                    out.push(ch);
                    i += 3;
                    continue;
                }
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

fn hex_val(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        b'A'..=b'F' => Some(b - b'A' + 10),
        _ => None,
    }
}

fn is_unreserved(b: u8) -> bool {
    b.is_ascii_alphanumeric() || matches!(b, b'-' | b'.' | b'_' | b'~')
}
