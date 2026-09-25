pub mod _legacy;
pub mod canonical;
pub mod crypto;
pub mod delegation;
pub mod export;
pub mod ingest;
pub mod snapshot;
pub mod staging;
pub mod types;
pub mod verify;

pub const DEFAULT_STAGING_PATH: &str = "/app/state/tuf-staging.json";
pub const DEFAULT_VERIFY_PATH: &str = "/app/state/verify-result.json";
pub const DEFAULT_REPORT_PATH: &str = "/app/output/delegation-report.json";
pub const DEFAULT_REJECTED_PATH: &str = "/app/output/rejected-targets.jsonl";
