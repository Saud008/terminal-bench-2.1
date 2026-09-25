//! Shared trace and report types.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "event", rename_all = "snake_case")]
pub enum TraceEvent {
    Rtt { seq: u64, rtt_us: u64 },
    Input {
        input_seq: u64,
        client_tick: u64,
    },
    InputAck {
        input_seq: u64,
        server_tick: u64,
    },
    LateFrame {
        frame_seq: u64,
    },
    SnapshotDelta {
        snapshot_seq: u64,
        base_seq: u64,
        state_xor: u64,
    },
    SnapshotGap {
        expected_seq: u64,
    },
    Reconnect {
        rollback_ticks: u64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimReport {
    pub lag_estimate_us: u64,
    pub lag_method: String,
    pub buffered_inputs_applied: u64,
    pub duplicate_inputs_skipped: u64,
    pub late_frames_rejected: u64,
    pub read_head: u64,
    pub rollback_window_ticks: u64,
    pub tick_rate_hz: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestManifest {
    pub trace_path: String,
    pub events_total: u64,
    pub read_head: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotRow {
    pub seq: u64,
    pub state_hash: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotBundle {
    pub snapshots: Vec<SnapshotRow>,
    pub merged_state_hash: u64,
    pub gap_fills: u64,
    pub integrity_chain: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportAudit {
    pub snapshot_count: u64,
    pub merged_state_hash: u64,
    pub integrity_chain: u64,
    pub export_seq: i64,
}
