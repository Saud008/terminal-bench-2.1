//! Building the Cookie header (RFC 6265 section 5.4).

use super::{order, Cookie, Jar};
use crate::cookie::path::path_match;
use crate::host::domain_match;
use crate::url::Url;

fn applies_to(c: &Cookie, url: &Url) -> bool {
    let domain_ok = url.host == c.domain || domain_match(&url.host, &c.domain);
    domain_ok && path_match(&url.path, &c.path) && (!c.secure || url.secure)
}

impl Jar {
    /// The Cookie header value for an HTTP request to `url` (empty when no
    /// cookie applies). Updates the last-access-time of every cookie sent.
    pub fn cookie_header(&mut self, url: &Url) -> String {
        self.purge_expired();
        let stamp = self.stamp();

        let mut hits: Vec<usize> = (0..self.cookies.len())
            .filter(|&i| applies_to(&self.cookies[i], url))
            .collect();
        order::sort(&mut hits, &self.cookies);

        let mut parts = Vec::with_capacity(hits.len());
        for &i in &hits {
            let c = &mut self.cookies[i];
            c.accessed = stamp;
            parts.push(format!("{}={}", c.name, c.value));
        }
        parts.join("; ")
    }
}
