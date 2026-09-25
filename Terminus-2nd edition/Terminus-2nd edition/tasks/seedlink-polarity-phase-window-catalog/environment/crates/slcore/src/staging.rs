use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::digest::compute_staging_digest;
use crate::error::SlError;
use crate::message::PickRow;
use crate::parse::parse_file;
use crate::polarity::effective_polarity;

pub const STAGING_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PhaseStaging {
    pub source: String,
    pub stem: String,
    pub staging_version: u32,
    pub network: String,
    pub station: String,
    pub epoch_sec: u32,
    pub leap_marker: u8,
    pub sample_count: u16,
    pub rate_mhz: u32,
    pub effective_polarity: i8,
    pub picks: Vec<PickRow>,
    pub digest: String,
}

pub fn staging_path(stem: &str) -> PathBuf {
    PathBuf::from("/app/state/phase-staging").join(format!("{stem}.json"))
}

pub fn stage_snippet(source: &Path, stem: &str) -> Result<PhaseStaging, SlError> {
    let msg = parse_file(source, false)?;
    let eff = effective_polarity(
        &msg.network,
        &msg.station,
        msg.body_polarity,
        None,
    )?;
    let mut picks = msg.picks.clone();
    picks.sort_by_key(|row| row.sample_idx);
    let digest = compute_staging_digest(&msg.picks, eff);
    Ok(PhaseStaging {
        source: source.display().to_string(),
        stem: stem.to_string(),
        staging_version: STAGING_VERSION,
        network: msg.network,
        station: msg.station,
        epoch_sec: msg.epoch_sec,
        leap_marker: msg.leap_marker,
        sample_count: msg.sample_count,
        rate_mhz: msg.rate_mhz,
        effective_polarity: eff,
        picks,
        digest,
    })
}

pub fn build_phase_staging(source: &Path, stem: &str) -> Result<PhaseStaging, SlError> {
    let stage = stage_snippet(source, stem)?;
    let path = staging_path(stem);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&path, serde_json::to_string_pretty(&stage)?)?;
    Ok(stage)
}

pub fn load_phase_staging(stem: &str) -> Result<PhaseStaging, SlError> {
    let path = staging_path(stem);
    if !path.is_file() {
        return Err(SlError::StagingMissing(path.display().to_string()));
    }
    let text = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&text)?)
}
