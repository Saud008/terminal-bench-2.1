#[path = "x7k/mod_a.rs"]
pub mod mod_a;
#[path = "n3p/mod_b.rs"]
pub mod mod_b;
#[path = "p9w/mod_c.rs"]
pub mod mod_c;
#[path = "q2r/mod_d.rs"]
pub mod mod_d;
#[path = "t5m/mod_e.rs"]
pub mod mod_e;
#[path = "u8j/mod_f.rs"]
pub mod mod_f;
#[path = "v1z/mod_g.rs"]
pub mod mod_g;
#[path = "decode/bundle.rs"]
pub mod decode_bundle;
#[path = "decoy/redaction.rs"]
pub mod decoy_redaction;
#[path = "model/custody_types.rs"]
pub mod custody_types;

pub const DEFAULT_BUNDLE_ROOT: &str = "/app/fixtures/cases";

pub fn bundle_root() -> String {
    std::env::var("TB3_CASE_ROOT").unwrap_or_else(|_| DEFAULT_BUNDLE_ROOT.to_string())
}
