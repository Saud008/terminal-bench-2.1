use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub chart_manifest_dir: String,
    pub tempo_stage_dir: String,
    pub grid_stage_dir: String,
    pub note_stage_dir: String,
    pub default_quant_divisor: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TempoEvent {
    pub tick: u64,
    pub microseconds_per_quarter: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeSig {
    pub tick: u64,
    pub numerator: u32,
    pub denominator: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NoteEvent {
    pub id: String,
    pub tick: u64,
    pub duration: u64,
    pub lane: u32,
    pub pitch: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChartDoc {
    pub chart_id: String,
    pub ppq: u32,
    pub quant_divisor: u32,
    pub tempo_events: Vec<TempoEvent>,
    pub time_sigs: Vec<TimeSig>,
    pub notes: Vec<NoteEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChartManifest {
    pub run_id: String,
    pub chart_id: String,
    pub ppq: u32,
    pub quant_divisor: u32,
    pub tempo_events: Vec<TempoEvent>,
    pub time_sigs: Vec<TimeSig>,
    pub notes: Vec<NoteEvent>,
    pub manifest_revision: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GridRow {
    pub tick: u64,
    pub seconds: f64,
    pub beat_index: f64,
    pub ticks_per_beat: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NoteStageRow {
    pub id: String,
    pub lane: u32,
    pub raw_tick: u64,
    pub quantized_tick: u64,
    pub rejected_overlap: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BeatGridAudit {
    pub run_id: String,
    pub chart_id: String,
    pub ppq: u32,
    pub tempo_event_count: u32,
    pub accepted_note_count: u32,
    pub rejected_overlap_count: u32,
    pub grid_consistency_score: f64,
    pub notes: Vec<NoteStageRow>,
    pub audit_digest: String,
}
