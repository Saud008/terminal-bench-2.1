#[path = "../lexfold_pkg/unicode.rs"]
pub mod token_unicode;
#[path = "../lexfold_pkg/punct.rs"]
pub mod token_punct;
#[path = "../wingram_pkg/window.rs"]
pub mod shingle_window;
#[path = "../rowmix_pkg/permutation.rs"]
pub mod hash_permutation;
#[path = "../rowmix_pkg/vector.rs"]
pub mod hash_vector;
#[path = "../ufmerge_pkg/threshold.rs"]
pub mod cluster_threshold;
#[path = "../ufmerge_pkg/representative.rs"]
pub mod cluster_representative;
#[path = "../snapcache_pkg/write.rs"]
pub mod sketch_write;
#[path = "../bundler_pkg/build.rs"]
pub mod graph_build;
#[path = "../sealrep_pkg/report.rs"]
pub mod attest_report;
#[path = "../corpus_io/load.rs"]
pub mod corpus_load;
#[path = "../decoy/lsh_telemetry.rs"]
pub mod decoy_lsh;
#[path = "../model/types.rs"]
pub mod types;

pub fn corpus_root() -> String {
    std::env::var("TB3_CORPUS_DIR").unwrap_or_else(|_| "/app/fixtures/corpora".to_string())
}

pub fn perm_salt() -> String {
    std::env::var("TB3_PERM_SALT").unwrap_or_default()
}
