use std::fs;
use std::path::Path;

use crate::errors::JitterError;
use crate::model::StagingFile;

pub fn write_staging(path: &str, staging: &StagingFile) -> Result<(), JitterError> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| JitterError::Io(e.to_string()))?;
    }
    let json = serde_json::to_string_pretty(staging).map_err(|e| JitterError::Parse(e.to_string()))?;
    fs::write(path, json).map_err(|e| JitterError::Io(e.to_string()))
}

pub fn read_staging(path: &str) -> Result<StagingFile, JitterError> {
    let bytes = fs::read(path).map_err(|e| JitterError::Io(e.to_string()))?;
    serde_json::from_slice(&bytes).map_err(|_| JitterError::InvalidStaging)
}
