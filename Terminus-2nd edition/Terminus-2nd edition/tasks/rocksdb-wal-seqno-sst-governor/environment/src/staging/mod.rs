use std::fs;
use std::path::Path;

use crate::types::StageFile;

pub fn load_stage(path: &str) -> Result<StageFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_stage(path: &str, stage: &StageFile) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(stage).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
