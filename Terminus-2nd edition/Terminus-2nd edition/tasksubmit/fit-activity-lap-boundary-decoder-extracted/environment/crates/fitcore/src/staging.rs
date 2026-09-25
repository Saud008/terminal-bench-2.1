use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::digest::compute_staging_digest;
use crate::error::FitError;
use crate::message::LapRow;
use crate::parse::parse_file;
use crate::trigger::classify_trigger;

pub const STAGING_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LapStaging {
    pub source: String,
    pub stem: String,
    pub staging_version: u32,
    pub laps: Vec<LapRow>,
    pub digest: String,
}

pub fn staging_path(stem: &str) -> PathBuf {
    PathBuf::from("/app/state/lap-staging").join(format!("{stem}.json"))
}

pub fn stage_laps(source: &Path, stem: &str) -> Result<LapStaging, FitError> {
    let mut rows: Vec<LapRow> = parse_file(source, false)?
        .into_iter()
        .map(|lap| LapRow {
            original_index: lap.original_index,
            start_time: lap.start_time,
            end_time: lap.end_time,
            distance_m: lap.distance_m,
            trigger: classify_trigger(lap.trigger_code),
            developer_note: lap.note,
        })
        .collect();
    rows.sort_by_key(|row| row.original_index);
    let digest = compute_staging_digest(&rows);
    Ok(LapStaging {
        source: source.display().to_string(),
        stem: stem.to_string(),
        staging_version: STAGING_VERSION,
        laps: rows,
        digest,
    })
}

pub fn build_lap_staging(source: &Path, stem: &str) -> Result<LapStaging, FitError> {
    let stage = stage_laps(source, stem)?;
    let path = staging_path(stem);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&path, serde_json::to_string_pretty(&stage)?)?;
    Ok(stage)
}

pub fn load_lap_staging(stem: &str) -> Result<LapStaging, FitError> {
    let path = staging_path(stem);
    if !path.is_file() {
        return Err(FitError::StagingMissing(path.display().to_string()));
    }
    let text = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&text)?)
}
