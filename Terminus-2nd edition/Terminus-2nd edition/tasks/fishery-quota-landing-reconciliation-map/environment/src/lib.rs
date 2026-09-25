pub mod atlas;
pub mod bind;
pub mod decoy;
pub mod harvest;
pub mod models;
pub mod policy;
pub mod taxon;
pub mod weight;

pub use atlas::quota_atlas;
pub use bind::bind_manifest;
pub use decoy::trawl_decoy;
pub use harvest::jsonl_harvest;
pub use policy::m2_gate as entitlement_window;
pub use policy::z9_zone as marine_closure;
pub use policy::r4_ledger as rollover_pool;
pub use taxon::k7_resolver as taxon_registry;
pub use weight::w3_coeff as round_weight;

pub const VAR_ROOT: &str = "/app/var";
pub const DEFAULT_FIXTURE_ROOT: &str = "/app/fixtures/seasons";
