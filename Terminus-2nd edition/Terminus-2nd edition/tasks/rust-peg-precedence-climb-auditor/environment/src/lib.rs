pub mod climb;
pub mod decoy;
pub mod export;
pub mod grammar;
pub mod ingest;
pub mod parse;
pub mod staging;
pub mod types;

pub const DEFAULT_GRAPH_PATH: &str = "/app/state/peg-rule-graph.json";
pub const DEFAULT_PARSE_PATH: &str = "/app/state/parse-tree.json";
pub const DEFAULT_AUDIT_PATH: &str = "/app/output/span-audit.json";
pub const DEFAULT_CHECKSUM_PATH: &str = "/app/output/span-checksum.txt";
