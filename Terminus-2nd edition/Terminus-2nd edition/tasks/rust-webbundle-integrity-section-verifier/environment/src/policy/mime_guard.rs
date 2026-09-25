pub fn mime_allowed(content_type: &str, allowed: &[String]) -> bool {
    allowed.iter().any(|m| m == content_type)
}

pub fn find_content_type(headers: &[(String, String)]) -> Option<String> {
    for (k, v) in headers {
        if k.eq_ignore_ascii_case("content-type") {
            return Some(v.clone());
        }
    }
    None
}
