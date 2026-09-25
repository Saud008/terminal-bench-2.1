#[path = "../c7_u9norm/convert.rs"]
pub mod c7_u9norm;
#[path = "../c7_p4bias/apply.rs"]
pub mod c7_p4bias;
#[path = "../c7_f2bind/map.rs"]
pub mod c7_f2bind;
#[path = "../c7_g5span/interp.rs"]
pub mod c7_g5span;
#[path = "../c7_h3score/score.rs"]
pub mod c7_h3score;
#[path = "../c7_l8emit/write.rs"]
pub mod c7_l8emit;
#[path = "../grade_decoy/estimate.rs"]
pub mod grade_decoy;
#[path = "../c7_f6rows/stage.rs"]
pub mod c7_f6rows;
#[path = "../c7_t6rows/stage.rs"]
pub mod c7_t6rows;
#[path = "../schema/kiln_types.rs"]
pub mod types;

pub fn fixture_root() -> String {
    std::env::var("TB3_FIXTURE_ROOT")
        .unwrap_or_else(|_| "/app/fixtures/kiln-runs".to_string())
}

pub fn cal_table_path() -> Option<String> {
    std::env::var("TB3_CAL_TABLE").ok()
}
