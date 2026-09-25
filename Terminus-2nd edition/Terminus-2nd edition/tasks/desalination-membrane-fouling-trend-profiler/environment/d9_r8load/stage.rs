// ingest stage: load hourly sensor CSV rows into the pressure buffer
use crate::types::{Config, StagedReading};
use std::collections::HashMap;
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn load_readings(
    cfg: &Config,
    run_id: &str,
    stream: &Path,
    cal_overrides: &HashMap<u32, f64>,
) -> Result<(), String> {
    let raw = fs::read_to_string(stream).map_err(|e| e.to_string())?;
    let mut rows = Vec::new();
    for line in raw.lines().skip(1) {
        let p: Vec<&str> = line.split(',').collect();
        if p.len() < 8 {
            continue;
        }
        let hour: u32 = p[0].parse().map_err(|_| "bad hour")?;
        let mut cal_offset: f64 = p[7].parse().map_err(|_| "bad cal offset")?;
        if let Some(off) = cal_overrides.get(&hour) {
            cal_offset = *off;
        }
        rows.push(StagedReading {
            hour_index: hour,
            batch_id: p[1].to_string(),
            pressure_bar: p[2].parse().map_err(|_| "bad pressure")?,
            salinity_ppt: p[3].parse().map_err(|_| "bad salinity")?,
            flow_m3h: p[4].parse().map_err(|_| "bad flow")?,
            temperature_c: p[5].parse().map_err(|_| "bad temp")?,
            sensor_flags: p[6].to_string(),
            cal_offset_ppt: cal_offset,
        });
    }
    let out = format!("{}/{}.jsonl", cfg.pressure_buffer_dir, run_id);
    let mut f = fs::File::create(&out).map_err(|e| e.to_string())?;
    writeln!(f, r#"{{"run_id":"{run_id}","stage":"pressure"}}"#).map_err(|e| e.to_string())?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
