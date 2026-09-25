#[path = "../bline_mf/parse.rs"]
pub mod bline_mf;
#[path = "../bline_pl/order.rs"]
pub mod bline_pl;
#[path = "../bline_wc/convert.rs"]
pub mod bline_wc;
#[path = "../bline_tm/meter.rs"]
pub mod bline_tm;
#[path = "../bline_qn/snap.rs"]
pub mod bline_qn;
#[path = "../bline_lg/reject.rs"]
pub mod bline_lg;
#[path = "../bline_ex/emit.rs"]
pub mod bline_ex;
#[path = "../harmony_decoy/harmony.rs"]
pub mod harmony_decoy;
#[path = "../model/chart_types.rs"]
pub mod types;

pub fn chart_root() -> String {
    std::env::var("TB3_CHART_DIR").unwrap_or_else(|_| "/app/fixtures/charts".to_string())
}

pub fn quant_divisor_override() -> Option<u32> {
    std::env::var("TB3_QUANT_DIVISOR")
        .ok()
        .and_then(|v| v.parse().ok())
}
