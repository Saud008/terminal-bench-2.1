pub mod mhz_peer;
pub mod geo_fence;
pub mod grants;
pub mod checkpoint;
pub mod tenure_gate;
pub mod carveout;
pub mod coupler;
pub mod rollup_emit;
pub mod decoy;
pub mod catalog_schema;

pub const DEFAULT_BUNDLE_ROOT: &str = "/opt/rflicat-bundles/bundles";

pub fn bundle_root() -> String {
    std::env::var("TB3_FIXTURE_DIR")
        .map(|d| format!("{d}/bundles"))
        .unwrap_or_else(|_| DEFAULT_BUNDLE_ROOT.to_string())
}
