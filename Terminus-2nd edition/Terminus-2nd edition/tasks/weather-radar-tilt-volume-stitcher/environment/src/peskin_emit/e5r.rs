// Volume metadata export report builder.
use crate::hopf_weave::weave;
use crate::models::{GateRecord, ScanBundle, StitchedReport};
use crate::ruelle_ratio::c6f;
use sha2::{Digest, Sha256};

pub fn build_stitched_report(token: &str, bundle: &ScanBundle, rows: &[GateRecord]) -> StitchedReport {
    let elevation_sequence: Vec<f64> = bundle
        .tilt_scans
        .iter()
        .map(|t| t.elevation_deg)
        .collect();
    let included: Vec<&GateRecord> = rows.iter().filter(|r| r.included).collect();
    let valid_gate_total = included.len() as u32;
    let mean_calibrated_dbz = if valid_gate_total == 0 {
        0.0
    } else {
        let sum: f64 = included.iter().map(|r| r.calibrated_dbz).sum();
        ((sum / valid_gate_total as f64) * 100.0).round() / 100.0
    };
    let azimuths: Vec<u32> = rows.iter().map(|r| r.azimuth_centideg).collect();
    let coverage_fraction = c6f::completeness_ratio(
        valid_gate_total,
        bundle.tilt_scans.len() as u32,
        &bundle.manifest,
    );
    let digest_body = serde_json::json!({
        "station_id": bundle.station.station_id,
        "valid_gate_total": valid_gate_total,
        "mean_calibrated_dbz": mean_calibrated_dbz,
        "coverage_fraction": coverage_fraction,
    });
    let report_digest = format!("{:x}", Sha256::digest(digest_body.to_string().as_bytes()));
    StitchedReport {
        run_token: token.to_string(),
        bundle_id: bundle.bundle_id.clone(),
        station_id: bundle.station.station_id.clone(),
        elevation_sequence,
        tilt_count: bundle.tilt_scans.len() as u32,
        valid_gate_total,
        mean_calibrated_dbz,
        coverage_fraction,
        azimuth_coverage_centideg: weave::azimuth_span_centideg(&azimuths),
        report_digest,
    }
}
