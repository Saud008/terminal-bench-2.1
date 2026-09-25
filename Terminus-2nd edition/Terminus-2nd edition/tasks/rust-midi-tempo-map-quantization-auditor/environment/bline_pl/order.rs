use crate::types::{Config, TempoEvent};
use std::fs;
use std::io::Write;

pub fn stage_tempo(cfg: &Config, run_id: &str, events: &[TempoEvent]) -> Result<(), String> {
    let mut ordered = events.to_vec();
    ordered.sort_by_key(|e| e.microseconds_per_quarter);
    let out = format!("{}/{}.jsonl", cfg.tempo_stage_dir, run_id);
    let mut f = fs::File::create(&out).map_err(|e| e.to_string())?;
    writeln!(f, "{{\"run_id\":\"{run_id}\",\"row_type\":\"header\"}}").map_err(|e| e.to_string())?;
    for ev in ordered {
        let js = serde_json::to_string(&ev).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
