#[path = "../tb3_mdist/dist.rs"]
pub mod tb3_mdist;
#[path = "../hx_place/roster.rs"]
pub mod hx_place;
#[path = "../tb3_sray/ray.rs"]
pub mod tb3_sray;
#[path = "../tb3_vlay/overlay.rs"]
pub mod tb3_vlay;
#[path = "../tb3_scope/reach.rs"]
pub mod tb3_scope;
#[path = "../tb3_rout/seal.rs"]
pub mod tb3_rout;
#[path = "../tb3_pclk/clock.rs"]
pub mod tb3_pclk;
#[path = "../scout_decoy/astar.rs"]
pub mod scout_decoy;
#[path = "../model/board_types.rs"]
pub mod types;

pub fn board_root() -> String {
    std::env::var("TB3_BOARD_DIR").unwrap_or_else(|_| "/app/fixtures/boards".to_string())
}
