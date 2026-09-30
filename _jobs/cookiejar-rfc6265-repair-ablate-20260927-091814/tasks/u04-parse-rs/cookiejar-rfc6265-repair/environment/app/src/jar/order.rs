use super::Cookie;

/// Orders the indices of the cookies going into one Cookie header.
pub fn sort(hits: &mut [usize], cookies: &[Cookie]) {
    hits.sort_by(|&a, &b| {
        let (a, b) = (&cookies[a], &cookies[b]);
        b.path.len().cmp(&a.path.len()).then_with(|| a.name.cmp(&b.name))
    });
}
