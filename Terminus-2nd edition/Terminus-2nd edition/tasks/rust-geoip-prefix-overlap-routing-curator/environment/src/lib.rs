#[path = "../netpfx/canon.rs"]
pub mod cidr_normalize;
#[path = "../netpfx/envelope.rs"]
pub mod cidr_contain;
#[path = "../rank_sel/tiebreak.rs"]
pub mod feed_tiebreak;
#[path = "../scope_fit/drop_ranges.rs"]
pub mod filter_reserved;
#[path = "../prov_chart/fork_log.rs"]
pub mod asn_lineage;
#[path = "../stg_wal/persist.rs"]
pub mod feed_cache_store;
#[path = "../reconcile/generation.rs"]
pub mod generation_store;
#[path = "../atlas_out/layout.rs"]
pub mod emit_order;
#[path = "../atlas_out/serialize.rs"]
pub mod emit_report;
#[path = "../ingest/bundle.rs"]
pub mod ingest_bundle;
#[path = "../model/overlap_model.rs"]
pub mod types;

pub const DEFAULT_BUNDLE_ROOT: &str = "/app/fixtures/bundles";

pub fn bundle_root() -> String {
    std::env::var("TB3_FIXTURE_DIR")
        .map(|d| format!("{d}/bundles"))
        .unwrap_or_else(|_| DEFAULT_BUNDLE_ROOT.to_string())
}

pub fn asn_salt() -> String {
    std::env::var("TB3_ASN_SALT").unwrap_or_default()
}
