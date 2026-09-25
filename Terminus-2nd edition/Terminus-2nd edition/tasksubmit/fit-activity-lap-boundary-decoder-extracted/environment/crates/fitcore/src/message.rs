use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapMsg {
    pub original_index: usize,
    pub start_time: u32,
    pub end_time: u32,
    pub distance_m: u16,
    pub trigger_code: u8,
    pub note: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct LapRow {
    pub original_index: usize,
    pub start_time: u32,
    pub end_time: u32,
    pub distance_m: u16,
    pub trigger: String,
    pub developer_note: String,
}
