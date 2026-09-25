#[path = "../internal/wv/qa.rs"]
pub mod wv_qa;
#[path = "../internal/wv/qb.rs"]
pub mod wv_qb;
#[path = "../internal/wv/qc.rs"]
pub mod wv_qc;
#[path = "../internal/wv/qd.rs"]
pub mod wv_qd;
#[path = "../internal/wv/qe.rs"]
pub mod wv_qe;
#[path = "../internal/wv/qf.rs"]
pub mod wv_qf;
#[path = "../internal/wv/qg.rs"]
pub mod wv_qg;
#[path = "../internal/wv/qh.rs"]
pub mod wv_qh;
#[path = "../internal/wv/qi.rs"]
pub mod wv_qi;
#[path = "../internal/wv/qj.rs"]
pub mod wv_qj;
#[path = "../shift_io/shift_bundle.rs"]
pub mod shift_io;
#[path = "../decoy/turbidity_chart.rs"]
pub mod decoy_chart;
#[path = "../protocol/plant_schema.rs"]
pub mod plant_schema;

pub const DEFAULT_SHIFT_ROOT: &str = "/app/fixtures/plant_shifts";

pub fn shift_root() -> String {
    std::env::var("TB3_FIXTURE_DIR")
        .map(|d| format!("{d}/plant_shifts"))
        .unwrap_or_else(|_| DEFAULT_SHIFT_ROOT.to_string())
}
