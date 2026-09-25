use std::collections::HashSet;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::SlError;
use crate::invariant::invariant_ok;
use crate::leap::load_leap_epochs;
use crate::message::PickRow;
use crate::parse::parse_file;
use crate::picks::{
    clipped_fraction, peak_amplitude, phase_label, pick_center_us, polarity_label, window_bounds,
};
use crate::staging::{build_phase_staging, stage_snippet, PhaseStaging, STAGING_VERSION};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PhaseWindow {
    pub phase: String,
    pub pick_sample: u16,
    pub center_us: u64,
    pub start_us: u64,
    pub end_us: u64,
    pub polarity: String,
    pub clipped_fraction: f64,
    pub peak_amplitude: i32,
    pub invariant_ok: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportReport {
    pub schema: String,
    pub source: String,
    pub stem: String,
    pub staging_version: u32,
    pub network: String,
    pub station: String,
    pub digest: String,
    pub window_count: usize,
    pub windows: Vec<PhaseWindow>,
}

pub fn build_export(staging: &PhaseStaging, msg_path: &Path) -> Result<ExportReport, SlError> {
    let msg = parse_file(msg_path, false)?;
    let leap_epochs = load_leap_epochs(None)?;
    let inv = invariant_ok(&staging.picks, staging.sample_count);
    let windows: Vec<PhaseWindow> = staging
        .picks
        .iter()
        .map(|pick| window_row(&msg, pick, staging.effective_polarity, &leap_epochs, inv))
        .collect();
    Ok(ExportReport {
        schema: "seedlink-phase-catalog/1".to_string(),
        source: staging.source.clone(),
        stem: staging.stem.clone(),
        staging_version: STAGING_VERSION,
        network: staging.network.clone(),
        station: staging.station.clone(),
        digest: staging.digest.clone(),
        window_count: windows.len(),
        windows,
    })
}

fn window_row(
    msg: &crate::message::SnippetMsg,
    pick: &PickRow,
    effective: i8,
    leap_epochs: &HashSet<u32>,
    inv: bool,
) -> PhaseWindow {
    let center = pick_center_us(msg, pick, leap_epochs);
    let (pre, post) = window_bounds(pick.phase_code);
    let peak = peak_amplitude(msg, pick, leap_epochs);
    PhaseWindow {
        phase: phase_label(pick.phase_code).to_string(),
        pick_sample: pick.sample_idx,
        center_us: center,
        start_us: center.saturating_sub(pre),
        end_us: center + post,
        polarity: polarity_label(effective, peak),
        clipped_fraction: clipped_fraction(msg, pick, leap_epochs),
        peak_amplitude: peak,
        invariant_ok: inv,
    }
}

pub fn export_from_staging(source: &str, stem: &str, msg_path: &Path) -> Result<ExportReport, SlError> {
    let staging = stage_snippet(msg_path, stem)?;
    if staging.source != source {
        return Err(SlError::StagingMismatch(format!(
            "source mismatch expected={source} got={}",
            staging.source
        )));
    }
    let report = build_export(&staging, msg_path)?;
    let out = Path::new("/app/output").join(format!("{stem}.json"));
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&out, serde_json::to_string_pretty(&report)?)?;
    Ok(report)
}

pub fn export_catalog(source: &Path, stem: &str) -> Result<ExportReport, SlError> {
    let stage_path = crate::staging::staging_path(stem);
    if !stage_path.is_file() {
        build_phase_staging(source, stem)?;
    }
    export_from_staging(&source.display().to_string(), stem, source)
}
