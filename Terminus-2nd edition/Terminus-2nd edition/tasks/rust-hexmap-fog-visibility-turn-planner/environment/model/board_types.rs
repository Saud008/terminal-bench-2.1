use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub board_roster_dir: String,
    pub los_ray_dir: String,
    pub fog_mask_dir: String,
    pub output_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cell {
    pub q: i32,
    pub r: i32,
    pub elev: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Unit {
    pub unit_id: String,
    pub q: i32,
    pub r: i32,
    pub class: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoardDoc {
    pub board_id: String,
    pub width_hint: u32,
    pub target_reveal: u32,
    pub cells: Vec<Cell>,
    pub units: Vec<Unit>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoardRoster {
    pub run_id: String,
    pub board_id: String,
    pub target_reveal: u32,
    pub fog_generation: u32,
    pub cells: Vec<Cell>,
    pub units: Vec<Unit>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RayRow {
    pub run_id: String,
    pub unit_id: String,
    pub q: i32,
    pub r: i32,
    pub in_radius: bool,
    pub clear_los: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FogMask {
    pub run_id: String,
    pub fog_generation: u32,
    pub visible_cells: Vec<CellRef>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct CellRef {
    pub q: i32,
    pub r: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FogAtlas {
    pub run_id: String,
    pub board_id: String,
    pub fog_generation: u32,
    pub target_reveal: u32,
    pub visible_count: u32,
    pub visible_cells: Vec<CellRef>,
    pub win_condition_met: bool,
}
