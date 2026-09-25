#[path = "../d9_r8load/stage.rs"]
pub mod d9_r8load;
#[path = "../d9_f1bind/stage.rs"]
pub mod d9_f1bind;
#[path = "../d9_p3norm/normalize.rs"]
pub mod d9_p3norm;
#[path = "../d9_c5anchor/anchor.rs"]
pub mod d9_c5anchor;
#[path = "../d9_m2lineage/map.rs"]
pub mod d9_m2lineage;
#[path = "../d9_g4bridge/bridge.rs"]
pub mod d9_g4bridge;
#[path = "../d9_s6trend/score.rs"]
pub mod d9_s6trend;
#[path = "../d9_l7emit/write.rs"]
pub mod d9_l7emit;
#[path = "../grade_decoy/plot.rs"]
pub mod grade_decoy;
#[path = "../schema/rotrace_types.rs"]
pub mod types;

pub fn fixture_root() -> String {
    std::env::var("TB3_FIXTURE_ROOT")
        .unwrap_or_else(|_| "/app/fixtures/ro-trains".to_string())
}

pub fn cal_table_path() -> Option<String> {
    std::env::var("TB3_CAL_TABLE").ok()
}
