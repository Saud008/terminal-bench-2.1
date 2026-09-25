pub fn normalize_headers(headers: &[(String, String)]) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = headers
        .iter()
        .map(|(k, v)| (k.to_ascii_lowercase(), v.trim().to_string()))
        .collect();
    out.sort_by(|a, b| a.0.cmp(&b.0));
    out
}

pub fn header_lines(headers: &[(String, String)]) -> String {
    normalize_headers(headers)
        .into_iter()
        .map(|(k, v)| format!("{k}:{v}"))
        .collect::<Vec<_>>()
        .join("
")
}
