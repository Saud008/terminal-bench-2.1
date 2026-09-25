use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct GateSample {
    pub range_bin: u32,
    pub dbz: f64,
    pub quality_mask: u8,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RaySample {
    pub azimuth_centideg: u32,
    pub gates: Vec<GateSample>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TiltScan {
    pub scan_id: String,
    pub elevation_deg: f64,
    pub channel: String,
    pub rays: Vec<RaySample>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StationMeta {
    pub station_id: String,
    pub calibration_offsets_dbz: BTreeMap<String, f64>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BundleManifest {
    pub expected_ray_count: u32,
    pub expected_gate_bins: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ScanBundle {
    pub bundle_id: String,
    pub station: StationMeta,
    pub manifest: BundleManifest,
    pub tilt_scans: Vec<TiltScan>,
}

#[derive(Debug, Clone, Serialize)]
pub struct GateRecord {
    pub scan_label: String,
    pub tilt_deg: f64,
    pub azimuth_centideg: u32,
    pub bridged_azimuth_centideg: u32,
    pub range_bin: u32,
    pub raw_dbz: f64,
    pub calibrated_dbz: f64,
    pub quality_mask: u8,
    pub included: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct StitchedReport {
    pub run_token: String,
    pub bundle_id: String,
    pub station_id: String,
    pub elevation_sequence: Vec<f64>,
    pub tilt_count: u32,
    pub valid_gate_total: u32,
    pub mean_calibrated_dbz: f64,
    pub coverage_fraction: f64,
    pub azimuth_coverage_centideg: u32,
    pub report_digest: String,
}
