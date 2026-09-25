//! Export-stage manifest digest helper (offline playtest seal reporting).
#![allow(dead_code)]

pub fn export_digest_label(checksum: &str) -> String {
    format!("export:{checksum}")
}
