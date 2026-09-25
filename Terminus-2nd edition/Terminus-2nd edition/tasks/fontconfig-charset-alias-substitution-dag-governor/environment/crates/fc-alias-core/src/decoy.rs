//! Decoy charset label normalizers — not used on compile or resolve export hot path.

pub fn fold_short_label(short: &str) -> String {
    short.to_ascii_lowercase()
}

pub fn strip_revision_suffix(name: &str) -> String {
    name.split(':').next().unwrap_or(name).to_string()
}
