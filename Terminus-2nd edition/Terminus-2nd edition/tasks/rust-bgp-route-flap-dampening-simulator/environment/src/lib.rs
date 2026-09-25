#[path = "../reports/sjsonl_emit.rs"]
pub mod atlas_emit;
#[path = "../lattice/hl_curve.rs"]
pub mod engine_decay;
#[path = "../timeline/ev_norm.rs"]
pub mod feed_normalize;
#[path = "../timeline/ev_sort.rs"]
pub mod feed_chrono;
#[path = "../timeline/ev_read.rs"]
pub mod feed_reader;
#[path = "../timeline/rtl_digest.rs"]
pub mod forecast_digest;
#[path = "../runloop/rtl_anchor.rs"]
pub mod forecast_anchor;
#[path = "../lattice/rtl_ms.rs"]
pub mod forecast_horizon;
#[path = "../reports/rtl_jsonl.rs"]
pub mod forecast_emit;
#[path = "../peers/rtl_pick.rs"]
pub mod forecast_pick;
#[path = "../runloop/ldg_store.rs"]
pub mod ledger_store;
#[path = "../runloop/lck_store.rs"]
pub mod lock_store;
#[path = "../peers/damp_row.rs"]
pub mod peer_table;
#[path = "../runloop/tick_adv.rs"]
pub mod drive_runner;
#[path = "../decoy/rib_decoy.rs"]
pub mod rib_decoy;
#[path = "../model/route_model.rs"]
pub mod route_model;
#[path = "../lattice/pfx_step.rs"]
pub mod prefix_steps;

pub mod forecast {
    pub use crate::forecast_digest as digest;
    pub use crate::forecast_emit as jsonl_out;
    pub use crate::forecast_anchor as anchor_bind;
    pub use crate::forecast_horizon as horizon_ms;
    pub use crate::forecast_pick as slot_pick;
}

pub const LOCK_PATH: &str = "/app/state/scenario-lock.json";
pub const LEDGER_PATH: &str = "/app/state/flap-ledger.json";
pub const RUN_COUNTER_PATH: &str = "/app/state/run-counter.json";
pub const DEFAULT_ROOT: &str = "/app/fixtures";

pub fn fixture_root() -> String {
    std::env::var("TB3_FIXTURE_DIR").unwrap_or_else(|_| DEFAULT_ROOT.to_string())
}

pub fn half_life_bias() -> i64 {
    std::env::var("TB3_HALF_LIFE_BIAS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0)
}
