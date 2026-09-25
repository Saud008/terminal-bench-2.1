pub mod bind;
pub mod wx_risk_blend;
pub mod wx_pair_journal;
pub mod decoy;
pub mod wx_plan_seal;
pub mod wx_temporal_pad;
pub mod pass_catalog;
pub mod pass_eligibility;
pub mod wx_rank_gate;
pub mod wx_schedule_core;
pub mod scenario_loader;
pub mod wx_mode_dwell;
pub mod tasking_types;

pub use bind::scenario_bind;
pub use wx_risk_blend::cloud_blend;
pub use wx_pair_journal::{write_plan_buffer, MatrixAuditMeta};
pub use decoy::kepler_propagate;
pub use wx_plan_seal::build_manifest;
pub use wx_temporal_pad::windows_overlap;
pub use pass_catalog::pass_index;
pub use pass_eligibility::eligible_passes;
pub use wx_rank_gate::{contract_rank, sort_requests};
pub use wx_schedule_core::resolve_plan;
pub use scenario_loader::read_scenario;
pub use wx_mode_dwell::setup_duration;

pub const VAR_ROOT: &str = "/app/var";
pub const DEFAULT_FIXTURE_ROOT: &str = "/app/fixtures/scenarios";
