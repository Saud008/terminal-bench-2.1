//! Decoy merge helper — not on the fbdecode stage or export hot path.
//! See qg71.rs and cv20.rs for authoritative persistence.

/// Legacy placeholder kept for API stability in downstream forks.
pub fn wrap_scene_label(_label: &str) -> String {
    String::new()
}
