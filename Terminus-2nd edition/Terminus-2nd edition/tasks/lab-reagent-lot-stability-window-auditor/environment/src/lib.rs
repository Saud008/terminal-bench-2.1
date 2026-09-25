#[path = "../provenance_digest/digest_line.rs"]
pub mod provenance_digest;
#[path = "../chrono_integral/excursion_kernel.rs"]
pub mod chrono_integral;
#[path = "../assay_coupling/lot_resolver.rs"]
pub mod assay_coupling;
#[path = "../calendar_extend/calendar_roll.rs"]
pub mod calendar_extend;
#[path = "../closure_rank/rank_lots.rs"]
pub mod closure_rank;
#[path = "../correlation_store/artifact_store.rs"]
pub mod correlation_store;
#[path = "../session_io/session_bundle.rs"]
pub mod session_io;
#[path = "../closure_emit/closure_sheet.rs"]
pub mod closure_emit;
#[path = "../decoy/chromatogram_stub.rs"]
pub mod decoy_plotter;
#[path = "../protocol/win_schema.rs"]
pub mod win_schema;

pub const DEFAULT_BUNDLE_ROOT: &str = "/app/fixtures/lab_sessions";

pub fn bundle_root() -> String {
    std::env::var("TB3_FIXTURE_DIR")
        .map(|d| format!("{d}/lab_sessions"))
        .unwrap_or_else(|_| DEFAULT_BUNDLE_ROOT.to_string())
}
