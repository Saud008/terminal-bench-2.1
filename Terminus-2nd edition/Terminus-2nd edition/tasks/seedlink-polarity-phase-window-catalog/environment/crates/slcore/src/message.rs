use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PickRow {
    pub sample_idx: u16,
    pub phase_code: u8,
}

#[derive(Debug, Clone)]
pub struct SnippetMsg {
    pub network: String,
    pub station: String,
    pub epoch_sec: u32,
    pub leap_marker: u8,
    pub sample_count: u16,
    pub rate_mhz: u32,
    pub body_polarity: i8,
    pub clip_mask: Vec<u8>,
    pub picks: Vec<PickRow>,
    pub samples: Vec<i16>,
}
