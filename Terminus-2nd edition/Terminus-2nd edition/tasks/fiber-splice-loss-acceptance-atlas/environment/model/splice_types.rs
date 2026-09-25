use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub capture_cache_dir: String,
    pub reflection_buffer_dir: String,
    pub topology_snapshot_dir: String,
    pub fixture_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureCache {
    pub run_id: String,
    pub trace_id: String,
    pub loss_threshold_db: f64,
    pub reflection_tolerance_m: f64,
    pub splices: Vec<SplicePlan>,
    pub load_generation: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplicePlan {
    pub distance_m: f64,
    pub splice_type: String,
    pub planned_loss_db: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SampleRow {
    pub distance_m: f64,
    pub power_dbm: f64,
    pub epoch: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LossEvent {
    pub distance_m: f64,
    pub measured_loss_db: f64,
    pub epoch: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteSegment {
    pub segment_id: String,
    pub start_m: f64,
    pub end_m: f64,
    pub connector_start: String,
    pub connector_end: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SegmentBind {
    pub segment_id: String,
    pub measured_loss_db: f64,
    pub connector_loss_db: f64,
    pub total_loss_db: f64,
    pub accepted: bool,
    pub bound_event_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BindStage {
    pub run_id: String,
    pub segments: Vec<SegmentBind>,
    pub suppressed_duplicate_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AcceptanceAtlas {
    pub run_id: String,
    pub event_count: u32,
    pub accepted_segment_count: u32,
    pub rejected_segment_count: u32,
    pub suppressed_duplicate_count: u32,
    pub segments: Vec<SegmentBind>,
    pub audit_digest: String,
}
