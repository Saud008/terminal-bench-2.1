use crate::win_schema::{CorrelatedLot, StabilityCorrelation};
use std::fs;
use std::path::Path;

pub fn write_correlation(
    path: &str,
    session_id: &str,
    bundle: &str,
    as_of_date: &str,
    prev_generation: u64,
    lots: Vec<CorrelatedLot>,
) -> Result<(), String> {
    let artifact = StabilityCorrelation {
        correlate_generation: prev_generation,
        session_id: session_id.to_string(),
        bundle: bundle.to_string(),
        as_of_date: as_of_date.to_string(),
        lots,
    };
    write_json(path, &artifact)
}

pub fn read_correlation(path: &str) -> Result<StabilityCorrelation, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn read_generation(path: &str) -> u64 {
    read_correlation(path)
        .map(|c| c.correlate_generation)
        .unwrap_or(0)
}

fn write_json(path: &str, v: &StabilityCorrelation) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}
")).map_err(|e| e.to_string())
}
