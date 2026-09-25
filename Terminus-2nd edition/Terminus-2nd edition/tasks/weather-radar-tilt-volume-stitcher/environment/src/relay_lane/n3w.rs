use crate::m2_table::p4s;
use crate::hopf_weave::weave;
use crate::stamp_z9::v7g;
use crate::models::{GateRecord, ScanBundle};
use sha2::{Digest, Sha256};

pub fn materialize_gates(bundle: &ScanBundle) -> Vec<GateRecord> {
    let mut rows = Vec::new();
    for tilt in &bundle.tilt_scans {
        for ray in &tilt.rays {
            let bridged = weave::unified_azimuth_centideg(ray.azimuth_centideg);
            for gate in &ray.gates {
                let calibrated = p4s::apply_offset(
                    gate.dbz,
                    &tilt.channel,
                    &bundle.station.calibration_offsets_dbz,
                );
                rows.push(GateRecord {
                    scan_label: tilt.scan_id.clone(),
                    tilt_deg: tilt.elevation_deg,
                    azimuth_centideg: ray.azimuth_centideg,
                    bridged_azimuth_centideg: bridged,
                    range_bin: gate.range_bin,
                    raw_dbz: gate.dbz,
                    calibrated_dbz: calibrated,
                    quality_mask: gate.quality_mask,
                    included: v7g::gate_is_valid(gate.quality_mask),
                });
            }
        }
    }
    rows
}

pub fn write_gate_buffer(
    token: &str,
    bundle: &ScanBundle,
    rows: &[GateRecord],
) -> Result<(String, u32), String> {
    let path = format!("{}/gate-buffer-{}.ndjson", crate::VAR_ROOT, token);
    let header_path = format!("{}/gate-buffer-{}.meta.json", crate::VAR_ROOT, token);
    let mut body = String::new();
    for row in rows {
        body.push_str(&serde_json::to_string(row).map_err(|e| e.to_string())?);
        body.push('\n');
    }
    std::fs::write(&path, &body).map_err(|e| e.to_string())?;
    let digest = format!("{:x}", Sha256::digest(body.as_bytes()));
    let header = serde_json::json!({
        "run_token": token,
        "bundle_id": bundle.bundle_id,
        "row_count": rows.len(),
        "ledger_fingerprint": digest,
    });
    std::fs::write(&header_path, serde_json::to_string_pretty(&header).unwrap())
        .map_err(|e| e.to_string())?;
    Ok((digest, rows.len() as u32))
}
