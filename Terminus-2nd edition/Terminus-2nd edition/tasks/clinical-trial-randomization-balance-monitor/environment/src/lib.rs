#[path = "../manifest/trial_digest.rs"]
pub mod trial_digest;
#[path = "../alpha/beta_norm.rs"]
pub mod beta_norm;
#[path = "../stratify/bucket_key.rs"]
pub mod bucket_key;
#[path = "../blocks/permuted_assign.rs"]
pub mod permuted_assign;
#[path = "../ceilings/limit_gate.rs"]
pub mod limit_gate;
#[path = "../closure/imbalance_ledger.rs"]
pub mod imbalance_ledger;
#[path = "../ledger/active_set.rs"]
pub mod active_set;
#[path = "../pipeline/compile_trial.rs"]
pub mod compile_trial;
#[path = "../pipeline/accept_log.rs"]
pub mod accept_log;
#[path = "../pipeline/run_balance.rs"]
pub mod run_balance;
#[path = "../pipeline/emit_closure.rs"]
pub mod emit_closure;
#[path = "../decoy/sample_size_prior.rs"]
pub mod sample_size_prior;

pub const LATCH_PATH: &str = "/app/state/trial-latch.json";
pub const CHRONICLE_PATH: &str = "/app/work/enrollment-chronicle.json";
pub const BALANCE_PATH: &str = "/app/work/balance-run.json";
pub const DEFAULT_ROOT: &str = "/app/fixtures";

pub fn fixture_root() -> String {
    std::env::var("TB3_FIXTURE_DIR").unwrap_or_else(|_| DEFAULT_ROOT.to_string())
}

pub fn trial_seed() -> u64 {
    std::env::var("RTBAL_TRIAL_SEED")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(77231)
}
