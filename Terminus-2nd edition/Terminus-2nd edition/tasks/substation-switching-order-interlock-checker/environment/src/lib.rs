pub mod yard_model;
pub mod scenario_loader;
pub mod bus_graph;
pub mod energize_propagate;
pub mod breaker_table;
pub mod loto_enforce;
pub mod mux_isolation;
pub mod procedure_steps;
pub mod proc_walk;
pub mod unsafe_explain;
pub mod diag_emit;
pub mod seq_anchor;
pub mod loto_ticket;
pub mod sublock_decoy_derate;
pub mod yard_bundle;
pub mod island_detect;

pub const DEFAULT_SCENARIO_ROOT: &str = "/app/fixtures/scenarios";

pub fn scenario_root() -> String {
    std::env::var("TB3_SCENARIO_DIR")
        .map(|d| format!("{d}/scenarios"))
        .unwrap_or_else(|_| DEFAULT_SCENARIO_ROOT.to_string())
}
