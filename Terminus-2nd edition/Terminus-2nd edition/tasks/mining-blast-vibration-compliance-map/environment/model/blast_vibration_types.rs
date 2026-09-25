use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub buffer_path: String,
    pub audit_passport_path: String,
    pub survey_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlastEvent {
    pub blast_id: String,
    pub easting_m: f64,
    pub northing_m: f64,
    pub source_ppv_mm_s: f64,
    pub fired_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyParcel {
    pub property_id: String,
    pub structure_class: String,
    pub boundary_vertices: Vec<[f64; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorCalibration {
    pub sensor_id: String,
    pub property_id: String,
    pub easting_m: f64,
    pub northing_m: f64,
    pub gain_multiplier: f64,
    pub zero_offset_mm_s: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeismoReading {
    pub blast_id: String,
    pub sensor_id: String,
    pub raw_ppv_mm_s: f64,
    pub peak_timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LimitTable {
    pub residential: LimitPair,
    pub industrial: LimitPair,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LimitPair {
    pub day_mm_s: f64,
    pub night_mm_s: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SurveyRecord {
    pub survey: String,
    pub reference_distance_m: f64,
    pub attenuation_exponent: f64,
    pub timezone_offset_hours: i32,
    pub blasts: Vec<BlastEvent>,
    pub properties: Vec<PropertyParcel>,
    pub sensors: Vec<SensorCalibration>,
    pub readings: Vec<SeismoReading>,
    pub limits: LimitTable,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeakCorrelationBuffer {
    pub correlate_seq: u64,
    pub seed: String,
    pub survey: String,
    pub record: SurveyRecord,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditPassportActive {
    pub seed: String,
    pub survey: String,
    pub audit_run_id: String,
    pub correlate_seq: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditPassport {
    pub active: Option<AuditPassportActive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExceedanceRow {
    pub blast_id: String,
    pub property_id: String,
    pub sensor_id: String,
    pub distance_m: f64,
    pub attenuated_ppv_mm_s: f64,
    pub threshold_mm_s: f64,
    pub exceedance_mm_s: f64,
    pub exceeded: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExceedanceSummary {
    pub reading_pairs: u32,
    pub exceedance_count: u32,
    pub max_exceedance_mm_s: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExceedanceAtlas {
    pub seed: String,
    pub survey: String,
    pub audit_run_id: String,
    pub exceedance_rows: Vec<ExceedanceRow>,
    pub summary: ExceedanceSummary,
    pub atlas_digest: String,
}
