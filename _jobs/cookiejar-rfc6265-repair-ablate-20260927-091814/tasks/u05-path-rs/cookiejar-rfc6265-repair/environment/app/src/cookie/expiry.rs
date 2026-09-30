use super::parse::Attr;

pub enum Lifetime {
    Session,
    Persistent(i64),
}

/// Lifetime of a new cookie from its attribute list (RFC 6265 section 5.3,
/// step 3).
pub fn resolve(attrs: &[Attr]) -> Lifetime {
    attrs
        .iter()
        .rev()
        .find_map(|a| match a {
            Attr::MaxAge(t) | Attr::Expires(t) => Some(*t),
            _ => None,
        })
        .map_or(Lifetime::Session, Lifetime::Persistent)
}
