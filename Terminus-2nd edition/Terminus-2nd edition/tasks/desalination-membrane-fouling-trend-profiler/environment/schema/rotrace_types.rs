use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub pressure_buffer_dir: String,
    pub cleaning_buffer_dir: String,
    pub ndp_grid_dir: String,
    pub trend_scratch_dir: String,
    pub default_slope_window_hours: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadingRow {
    pub hour_index: u32,
    pub batch_id: String,
    pub pressure_bar: f64,
    pub salinity_ppt: f64,
    pub flow_m3h: f64,
    pub temperature_c: f64,
    pub sensor_flags: String,
    pub cal_offset_ppt: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedReading {
    pub hour_index: u32,
    pub batch_id: String,
    pub pressure_bar: f64,
    pub salinity_ppt: f64,
    pub flow_m3h: f64,
    pub temperature_c: f64,
    pub sensor_flags: String,
    pub cal_offset_ppt: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MembraneBatch {
    pub batch_id: String,
    pub parent_batch_id: Option<String>,
    pub alpha: Option<f64>,
    pub beta: Option<f64>,
    pub p_base: Option<f64>,
    pub t_ref: Option<f64>,
    pub q_ref: Option<f64>,
    pub active_from_hour: u32,
    pub active_until_hour: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleaningEvent {
    pub hour_index: u32,
    pub event_type: String,
    pub cleaned_on: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleaningBuffer {
    pub run_id: String,
    pub train_id: String,
    pub membrane_id: String,
    pub batches: Vec<MembraneBatch>,
    pub cleaning_events: Vec<CleaningEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NdpGridRow {
    pub hour_index: u32,
    pub batch_id: String,
    pub ndp: f64,
    pub salinity_ppt: f64,
    pub pressure_bar: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrendScratchRow {
    pub hour_index: u32,
    pub batch_id: String,
    pub ndp: f64,
    pub trend_class: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrendScratch {
    pub run_id: String,
    pub slope_window_hours: u32,
    pub rows: Vec<TrendScratchRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChronicleRow {
    pub hour_index: u32,
    pub batch_id: String,
    pub ndp: f64,
    pub trend_class: String,
    pub element_fp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChronicleSummary {
    pub total_readings: u32,
    pub critical_count: u32,
    pub accelerating_count: u32,
    pub stable_count: u32,
    pub max_ndp: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FoulingTrendChronicle {
    pub run_id: String,
    pub train_id: String,
    pub chronicle_rows: Vec<ChronicleRow>,
    pub summary: ChronicleSummary,
    pub batch_lineage_digest: String,
    pub chronicle_digest: String,
}
