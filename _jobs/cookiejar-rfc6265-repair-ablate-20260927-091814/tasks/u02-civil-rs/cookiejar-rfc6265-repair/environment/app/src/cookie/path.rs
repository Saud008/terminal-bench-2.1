//! Paths and path-match (RFC 6265 section 5.1.4).

/// The default-path of a request-uri path.
pub fn default_path(uri_path: &str) -> String {
    if !uri_path.starts_with('/') {
        return "/".to_string();
    }
    match uri_path.rfind('/') {
        Some(0) | None => "/".to_string(),
        Some(i) => uri_path[..=i].to_string(),
    }
}

pub fn path_match(request_path: &str, cookie_path: &str) -> bool {
    request_path.starts_with(cookie_path)
}
