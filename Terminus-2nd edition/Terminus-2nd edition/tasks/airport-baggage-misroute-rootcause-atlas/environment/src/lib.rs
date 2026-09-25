#[path = "../ingress_normalizer/ingress.rs"]
pub mod ingress_normalizer;
#[path = "../belt_matrix/select.rs"]
pub mod belt_matrix;
#[path = "../gap_evaluator/feasible.rs"]
pub mod gap_evaluator;
#[path = "../suppress_filter/window.rs"]
pub mod suppress_filter;
#[path = "../cause_rank/rank.rs"]
pub mod cause_rank;
#[path = "../output_facet/write_doc.rs"]
pub mod output_facet;
#[path = "../weight_decoy/forecast.rs"]
pub mod weight_decoy;
#[path = "../model/hub_records.rs"]
pub mod types;

pub fn hub_root() -> String {
    std::env::var("TB3_HUB_ROOT").unwrap_or_else(|_| "/app/fixtures/hubs".to_string())
}

pub fn mct_override() -> Option<u64> {
    std::env::var("TB3_MCT_MINUTES").ok().and_then(|v| v.parse().ok())
}

pub fn outage_station_override() -> Option<String> {
    std::env::var("TB3_OUTAGE_STATION").ok()
}
