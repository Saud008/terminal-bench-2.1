//! Which hosts a new cookie is scoped to (RFC 6265 section 5.3, steps 4-6).

use super::parse::Attr;
use crate::host::domain_match;
use crate::psl::List;

pub enum Scope {
    /// Only sent back to exactly this host.
    HostOnly(String),
    /// Sent to this domain and every subdomain of it.
    Domain(String),
}

/// `None` means the cookie must be ignored.
pub fn resolve(attrs: &[Attr], host: &str, psl: &List) -> Option<Scope> {
    let domain = attrs
        .iter()
        .rev()
        .find_map(|a| match a {
            Attr::Domain(d) => Some(d.clone()),
            _ => None,
        })
        .unwrap_or_default();

    if !domain.is_empty() && psl.is_public_suffix(&domain) {
        return None;
    }

    if domain.is_empty() {
        return Some(Scope::HostOnly(host.to_string()));
    }
    if !domain_match(host, &domain) {
        return None;
    }
    Some(Scope::Domain(domain))
}
