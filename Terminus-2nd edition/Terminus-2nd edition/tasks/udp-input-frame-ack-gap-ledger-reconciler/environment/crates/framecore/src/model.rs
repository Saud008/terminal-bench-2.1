use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BundleSpec {
    pub bundle_id: String,
    pub description: String,
    pub packets: Vec<PacketSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PacketSpec {
    pub hex: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SimInput {
    pub tick_offset: u16,
    pub opcode: u8,
    pub value: i16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WireFrame {
    pub client_id: u32,
    pub frame_seq: u32,
    pub ack_base: u32,
    pub loss_mask: u64,
    pub base_tick: u32,
    pub inputs: Vec<SimInput>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GapRange {
    pub start: u32,
    pub end: u32,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct LedgerExport {
    pub playhead: u32,
    pub gaps: Vec<GapRange>,
    pub duplicate_acks: u32,
    pub peer_loss_gaps: Vec<GapRange>,
    pub frames_received: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SimExport {
    pub tick: u64,
    pub accumulator: i64,
    pub mix: u64,
    pub inputs_applied: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReplayExport {
    pub bundle_id: String,
    pub seed: u64,
    pub client_id: u32,
    pub state_hash: String,
    pub ledger: LedgerExport,
    pub sim: SimExport,
}

#[derive(Debug, Clone, Default)]
pub struct SimState {
    pub tick: u64,
    pub accumulator: i64,
    pub mix: u64,
    pub inputs_applied: u32,
}

#[derive(Debug, Clone, Default)]
pub struct LedgerState {
    pub playhead: u32,
    pub seen: std::collections::BTreeSet<u32>,
    pub gaps: Vec<(u32, u32)>,
    pub duplicate_acks: u32,
    pub peer_loss_gaps: Vec<(u32, u32)>,
    pub frames_received: u32,
}
