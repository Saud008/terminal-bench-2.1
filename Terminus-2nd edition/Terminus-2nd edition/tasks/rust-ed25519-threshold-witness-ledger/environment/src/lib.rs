pub mod bundle;
pub mod canonical;
pub mod crypto;
pub mod emit;
pub mod ledger;
pub mod quorum;
pub mod types;
pub mod wrap;

pub const DEFAULT_STAGING_PATH: &str = "/app/state/tw-approval-stage.json";
pub const DEFAULT_VERDICT_PATH: &str = "/app/state/quorum-verdict.json";
pub const DEFAULT_LEDGER_PATH: &str = "/app/output/release-witness-ledger.json";
