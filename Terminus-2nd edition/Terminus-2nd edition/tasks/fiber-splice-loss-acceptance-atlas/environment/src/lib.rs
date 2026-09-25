#[path = "../bundle_latch/latch.rs"]
pub mod bundle_latch;
#[path = "../morlet_scan/scan.rs"]
pub mod morlet_scan;
#[path = "../hopf_fold/fold.rs"]
pub mod hopf_fold;
#[path = "../route_weave/weave.rs"]
pub mod route_weave;
#[path = "../junction_ledger/budget.rs"]
pub mod junction_ledger;
#[path = "../atlas_emit/emit.rs"]
pub mod atlas_emit;
#[path = "../tf_decoy/decoy.rs"]
pub mod tf_decoy;
#[path = "../model/splice_types.rs"]
pub mod types;

pub fn loss_threshold_override() -> Option<f64> {
    std::env::var("TB3_LOSS_THRESHOLD_DB")
        .ok()
        .and_then(|v| v.parse().ok())
}

pub fn reflection_tol_override() -> Option<f64> {
    std::env::var("TB3_REFLECTION_TOLERANCE_M")
        .ok()
        .and_then(|v| v.parse().ok())
}
