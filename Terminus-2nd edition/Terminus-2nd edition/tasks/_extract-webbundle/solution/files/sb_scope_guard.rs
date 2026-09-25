use crate::url_norm::canonical_url;

pub fn url_in_scope(url: &str, scopes: &[String]) -> bool {
    let canon = canonical_url(url);
    for scope in scopes {
        let sc = canonical_url(scope);
        if sc.ends_with('/') {
            if canon.starts_with(&sc) {
                return true;
            }
        } else if canon == sc {
            return true;
        } else if canon.starts_with(&sc) {
            let next = canon.chars().nth(sc.len());
            if next == Some('/') {
                return true;
            }
        }
    }
    false
}

pub fn scope_violations(url: &str, scopes: &[String]) -> bool {
    !url_in_scope(url, scopes)
}
