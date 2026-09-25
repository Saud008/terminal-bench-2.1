use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::FitError;
use crate::message::LapRow;
use crate::staging::{build_lap_staging, load_lap_staging, stage_laps, LapStaging};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportLap {
    pub lap_index: usize,
    pub start_time: u32,
    pub end_time: u32,
    pub duration_s: u32,
    pub distance_m: u16,
    pub trigger: String,
    pub developer_note: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportReport {
    pub schema: String,
    pub source: String,
    pub stem: String,
    pub staging_version: u32,
    pub lap_count: usize,
    pub digest: String,
    pub laps: Vec<ExportLap>,
}

pub fn build_export(staging: &LapStaging) -> Result<ExportReport, FitError> {
    let laps = staging
        .laps
        .iter()
        .enumerate()
        .map(|(lap_index, row)| lap_row_to_export(lap_index, row))
        .collect();
    Ok(ExportReport {
        schema: "fit-lap-export/1".to_string(),
        source: staging.source.clone(),
        stem: staging.stem.clone(),
        staging_version: staging.staging_version,
        lap_count: staging.laps.len(),
        digest: staging.digest.clone(),
        laps,
    })
}

pub fn export_from_staging(source: &str, stem: &str) -> Result<ExportReport, FitError> {
    let parsed = stage_laps(Path::new(source), stem)?;
    let report = build_export(&parsed)?;
    let out = Path::new("/app/output").join(format!("{stem}.json"));
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&out, serde_json::to_string_pretty(&report)?)?;
    Ok(report)
}

pub fn export_laps(source: &Path, stem: &str) -> Result<ExportReport, FitError> {
    let stage_path = crate::staging::staging_path(stem);
    if !stage_path.is_file() {
        build_lap_staging(source, stem)?;
    }
    export_from_staging(&source.display().to_string(), stem)
}

fn lap_row_to_export(lap_index: usize, row: &LapRow) -> ExportLap {
    ExportLap {
        lap_index,
        start_time: row.start_time,
        end_time: row.end_time,
        duration_s: row.end_time.saturating_sub(row.start_time),
        distance_m: row.distance_m,
        trigger: row.trigger.clone(),
        developer_note: row.developer_note.clone(),
    }
}

#[allow(dead_code)]
fn _load_direct(stem: &str) -> Result<LapStaging, FitError> {
    load_lap_staging(stem)
}
