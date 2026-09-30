//! Storage model (RFC 6265 section 5.3).

use super::{Cookie, Jar};
use crate::cookie::domain::{self, Scope};
use crate::cookie::expiry::{self, Lifetime};
use crate::cookie::parse::{self, Attr};
use crate::cookie::path::default_path;
use crate::url::Url;

impl Jar {
    /// Handles a Set-Cookie header received in the response to `url`.
    pub fn set_cookie(&mut self, url: &Url, header: &str) {
        let Some(sc) = parse::parse(header, url, self.clock) else {
            return;
        };
        let Some(scope) = domain::resolve(&sc.attrs, &url.host, &self.psl) else {
            return;
        };
        let (domain, host_only) = match scope {
            Scope::HostOnly(h) => (h, true),
            Scope::Domain(d) => (d, false),
        };
        let path = sc
            .attrs
            .iter()
            .rev()
            .find_map(|a| match a {
                Attr::Path(p) => Some(p.clone()),
                _ => None,
            })
            .unwrap_or_else(|| default_path(&url.path));
        let expiry = match expiry::resolve(&sc.attrs) {
            Lifetime::Session => None,
            Lifetime::Persistent(t) => Some(t),
        };
        let secure = sc.attrs.iter().any(|a| matches!(a, Attr::Secure));
        let http_only = sc.attrs.iter().any(|a| matches!(a, Attr::HttpOnly));

        let stamp = self.stamp();
        let site = self.psl.registrable_domain(&domain);

        if let Some(i) = self
            .cookies
            .iter()
            .position(|c| c.name == sc.name && c.domain == domain && c.path == path)
        {
            self.cookies.remove(i);
        }

        self.cookies.push(Cookie {
            name: sc.name,
            value: sc.value,
            domain,
            path,
            expiry,
            host_only,
            secure,
            http_only,
            created: stamp,
            accessed: stamp,
        });

        self.purge_expired();
        self.enforce_site_limit(&site);
    }
}
