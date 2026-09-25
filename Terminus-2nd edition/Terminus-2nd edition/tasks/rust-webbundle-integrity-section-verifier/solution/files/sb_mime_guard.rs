pub fn mime_allowed(content_type: &str, allowed: &[String]) -> bool {
    let base = content_type.split(';').next().unwrap_or(content_type).trim().to_ascii_lowercase();
    allowed.iter().any(|m| m.to_ascii_lowercase() == base)
}

pub fn find_content_type(headers: &[(String, String)]) -> Option<String> {
    for (k, v) in headers {
        if k.eq_ignore_ascii_case("content-type") {
            return Some(v.clone());
        }
    }
    None
}
