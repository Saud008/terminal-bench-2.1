pub mod rail_model;
pub mod scenario_io;
pub mod adj_walk;
pub mod span_math;
pub mod aspect_rule;
pub mod rank_filter;
pub mod topo_persist;
pub mod part_sort;
pub mod ledger_emit;
pub mod authority_ticket;
pub mod rail_decoy_aspect;
pub mod track_load;

pub const DEFAULT_SCENARIO_ROOT: &str = "/app/fixtures/scenarios";

pub fn scenario_root() -> String {
    std::env::var("TB3_SCENARIO_DIR")
        .map(|d| format!("{d}/scenarios"))
        .unwrap_or_else(|_| DEFAULT_SCENARIO_ROOT.to_string())
}

pub fn zone_salt() -> String {
    std::env::var("TB3_ZONE_SALT").unwrap_or_default()
}
