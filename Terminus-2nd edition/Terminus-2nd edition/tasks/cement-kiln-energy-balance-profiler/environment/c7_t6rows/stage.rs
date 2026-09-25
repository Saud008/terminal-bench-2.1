use crate::c7_u9norm;
use crate::types::{Config, StagedTelemetry, TelemetryRow};
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn load_probes(
    cfg: &Config,
    run_id: &str,
    telemetry: &Path,
    cal_overrides: &[(String, f64)],
) -> Result<(), String> {
    let raw = fs::read_to_string(telemetry).map_err(|e| e.to_string())?;
    let mut rows = Vec::new();
    for line in raw.lines().skip(1) {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() < 5 {
            continue;
        }
        rows.push(TelemetryRow {
            probe_id: parts[0].to_string(),
            probe_ts: parts[1].parse().map_err(|_| "bad ts")?,
            temp_raw: parts[2].parse().map_err(|_| "bad temp")?,
            unit: parts[3].to_string(),
            cal_offset_c: parts[4].parse().map_err(|_| "bad offset")?,
        });
    }
    for row in &mut rows {
        if let Some((_, off)) = cal_overrides.iter().find(|(p, _)| p == &row.probe_id) {
            row.cal_offset_c = *off;
        }
    }
    let out = format!("{}/{}.jsonl", cfg.tele_buffer_dir, run_id);
    let mut f = fs::File::create(&out).map_err(|e| e.to_string())?;
    writeln!(f, r#"{{"run_id":"{run_id}","stage":"telemetry"}}"#).map_err(|e| e.to_string())?;
    for row in rows {
        let norm = c7_u9norm::normalize_to_celsius(row.temp_raw, &row.unit);
        let staged = StagedTelemetry {
            probe_id: row.probe_id.clone(),
            probe_ts: row.probe_ts,
            temp_norm_c: norm,
            cal_offset_c: row.cal_offset_c,
        };
        let js = serde_json::to_string(&staged).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
