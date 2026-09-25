use crate::types::{PeakCorrelationBuffer, SurveyRecord};
use std::fs;
use std::path::Path;

pub fn write_buffer(path: &str, seed: &str, record: &SurveyRecord) -> Result<(), String> {
    let prev = read_buffer(path).ok();
    let correlate_seq = prev.map(|b| b.correlate_seq).unwrap_or(0) + 1;
    let buf = PeakCorrelationBuffer {
        correlate_seq,
        seed: seed.to_string(),
        survey: record.survey.clone(),
        record: record.clone(),
    };
    write_file(path, &buf)
}

pub fn read_buffer(path: &str) -> Result<PeakCorrelationBuffer, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_seed_survey(buf: &PeakCorrelationBuffer, seed: &str, survey: &str) -> Result<(), String> {
    if buf.seed != seed || buf.survey != survey {
        return Err("buffer seed/survey mismatch".into());
    }
    Ok(())
}

fn write_file(path: &str, buf: &PeakCorrelationBuffer) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(buf).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
