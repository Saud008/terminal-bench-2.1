#[path = "../line_validity/validity_line.rs"]
pub mod line_validity;
#[path = "../walk_parent/chain_walk.rs"]
pub mod walk_parent;
#[path = "../budget_rss/combine.rs"]
pub mod budget_rss;
#[path = "../gate_operator/authorize.rs"]
pub mod gate_operator;
#[path = "../matrix_limits/band.rs"]
pub mod matrix_limits;
#[path = "../register_store/register_db.rs"]
pub mod register_store;
#[path = "../vault_snapshot/vault_write.rs"]
pub mod vault_snapshot;
#[path = "../row_publish/publish.rs"]
pub mod row_publish;
#[path = "../run_io/pack_loader.rs"]
pub mod run_io;
#[path = "../meter_parse/reading_norm.rs"]
pub mod meter_parse;
#[path = "../decoy/spectrum_stub.rs"]
pub mod decoy_plotter;
#[path = "../protocol/chain_schema.rs"]
pub mod chain_schema;

pub const DEFAULT_FIXTURE_ROOT: &str = "/app/fixtures/cal_runs";

pub fn fixture_root() -> String {
    std::env::var("TB3_FIXTURE_DIR")
        .map(|d| format!("{d}/cal_runs"))
        .unwrap_or_else(|_| DEFAULT_FIXTURE_ROOT.to_string())
}
