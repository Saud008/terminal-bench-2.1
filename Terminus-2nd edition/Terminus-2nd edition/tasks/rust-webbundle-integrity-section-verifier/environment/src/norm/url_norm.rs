pub fn canonical_url(raw: &str) -> String {
    let (scheme, rest) = match raw.split_once("://") {
        Some((s, r)) => (s.to_lowercase(), r),
        None => ("http".to_string(), raw),
    };
    let (host_port, path_query) = match rest.split_once('/') {
        Some((h, p)) => (h, format!("/{p}")),
        None => (rest, "/".to_string()),
    };
    let host = host_port.split(':').next().unwrap_or(host_port).to_string();
    let mut path = path_query;
    if path.is_empty() {
        path = "/".to_string();
    }
    let (path_only, query) = match path.split_once('?') {
        Some((p, q)) => (p.to_string(), Some(q.to_string())),
        None => (path, None),
    };
    let mut out = format!("{scheme}://{host}{path_only}");
    if let Some(q) = query {
        out.push('?');
        out.push_str(&q);
    }
    out
}
