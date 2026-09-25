use crate::types::{CleaningBuffer, CleaningEvent, Config, MembraneBatch};
use std::fs;
use std::path::Path;

pub fn bind_cleaning(
    cfg: &Config,
    run_id: &str,
    events_path: &Path,
    membrane_path: &Path,
    train_id: &str,
) -> Result<(), String> {
    let events_raw = fs::read_to_string(events_path).map_err(|e| e.to_string())?;
    let mut cleaning_events = Vec::new();
    for line in events_raw.lines().skip(1) {
        let p: Vec<&str> = line.split(',').collect();
        if p.len() < 3 {
            continue;
        }
        cleaning_events.push(CleaningEvent {
            hour_index: p[0].parse().map_err(|_| "bad hour")?,
            event_type: p[1].to_string(),
            cleaned_on: p[2].to_string(),
        });
    }
    let membrane_raw = fs::read_to_string(membrane_path).map_err(|e| e.to_string())?;
    let doc: serde_json::Value = serde_json::from_str(&membrane_raw).map_err(|e| e.to_string())?;
    let batches: Vec<MembraneBatch> =
        serde_json::from_value(doc["batches"].clone()).map_err(|e| e.to_string())?;
    let membrane_id = batches
        .first()
        .map(|b| b.batch_id.clone())
        .unwrap_or_else(|| "MEM-UNKNOWN".to_string());
    let body = CleaningBuffer {
        run_id: run_id.to_string(),
        train_id: train_id.to_string(),
        membrane_id,
        batches,
        cleaning_events,
    };
    let out = format!("{}/{}.json", cfg.cleaning_buffer_dir, run_id);
    fs::write(&out, serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    Ok(())
}
