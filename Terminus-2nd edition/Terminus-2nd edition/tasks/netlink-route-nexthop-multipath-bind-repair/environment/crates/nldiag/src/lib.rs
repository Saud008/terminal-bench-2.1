//! Standalone nldiag crate — not linked into nlctl.
//! Exists so lab operators can experiment with dump headers offline.

pub fn banner() -> &'static str {
    "nldiag-offline"
}
