#[path = "ak01/wire_body.rs"]
pub mod crypto_authdata;
#[path = "ak01/x509.rs"]
pub mod crypto_x509;
#[path = "ak02/vendor_map.rs"]
pub mod registry_aaguid;
#[path = "ak03/uv_gate.rs"]
pub mod policy_uv;
#[path = "ak04/sign_row.rs"]
pub mod replay_cred;
#[path = "ak05/row_seq.rs"]
pub mod cache_batch;
#[path = "ak06/emit.rs"]
pub mod trust_emit;
#[path = "decode/bundle.rs"]
pub mod decode_bundle;
#[path = "decoy/heatmap.rs"]
pub mod decoy_heatmap;
#[path = "model/attest_model.rs"]
pub mod attest_model;

pub const DEFAULT_BUNDLE_ROOT: &str = "/app/registry/transcript-bundles";

pub fn bundle_root() -> String {
    std::env::var("TB3_REGISTRY_ROOT")
        .map(|d| format!("{d}/transcript-bundles"))
        .unwrap_or_else(|_| DEFAULT_BUNDLE_ROOT.to_string())
}

pub fn metadata_path(cfg: &crate::attest_model::Config) -> String {
    std::env::var("TB3_METADATA_PATH").unwrap_or_else(|_| {
        std::env::var("TB3_REGISTRY_ROOT")
            .map(|d| format!("{d}/authenticators/aaguid-registry.json"))
            .unwrap_or_else(|_| cfg.metadata_path.clone())
    })
}
