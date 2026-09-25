use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RawFrame {
    pub offset: usize,
    pub header_len: u8,
    pub incompat: u8,
    pub compat: u8,
    pub seq: u8,
    pub sysid: u8,
    pub compid: u8,
    pub msg_id: u32,
    pub payload: Vec<u8>,
    pub crc_wire: u16,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ValidatedFrame {
    pub msg_id: u32,
    pub name: String,
    pub sysid: u8,
    pub compid: u8,
    pub seq: u8,
    pub payload: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RouteCount {
    pub sysid: u8,
    pub compid: u8,
    pub msg_id: u32,
    pub name: String,
    pub count: u32,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GpsFix {
    pub sysid: u8,
    pub compid: u8,
    pub seq: u8,
    pub time_boot_ms: u32,
    pub lat: i32,
    pub lon: i32,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EventLog {
    pub sysid: u8,
    pub compid: u8,
    pub frame_seq: u8,
    pub timestamp_ms: u32,
    pub event_seq: u16,
    pub value: i16,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiffRow {
    pub sysid: u8,
    pub compid: u8,
    pub msg_id: u32,
    pub fact_key: String,
    pub old_value: Option<String>,
    pub new_value: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DecodeSnapshot {
    pub version: u32,
    pub seed: String,
    pub checkpoint_frame_count: u32,
    pub deduped_count: u32,
    pub stale_seq_dropped: u32,
    pub changed_fact_count: u32,
    pub diff_rows: Vec<DiffRow>,
    pub frames: Vec<ValidatedFrame>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExportDoc {
    pub seed: String,
    pub valid_frame_count: u32,
    pub checkpoint_frame_count: u32,
    pub deduped_count: u32,
    pub stale_seq_dropped: u32,
    pub changed_fact_count: u32,
    pub diff_rows: Vec<DiffRow>,
    pub routes: Vec<RouteCount>,
    pub gps_fixes: Vec<GpsFix>,
    pub events: Vec<EventLog>,
}
