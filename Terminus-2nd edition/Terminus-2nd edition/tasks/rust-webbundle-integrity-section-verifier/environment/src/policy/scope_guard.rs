use crate::url_norm::canonical_url;

pub fn url_in_scope(url: &str, scopes: &[String]) -> bool {
    let canon = canonical_url(url);
    for scope in scopes {
        if canon.starts_with(scope) {
            return true;
        }
    }
    false
}

pub fn scope_violations(url: &str, scopes: &[String]) -> bool {
    !url_in_scope(url, scopes)
}
