use std::fs;
use std::path::Path;

use crate::types::PackStage;

pub fn load_stage(path: &str) -> Result<PackStage, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_stage(path: &str, stage: &PackStage) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(stage).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn bump_ingest_seq(path: &str) -> u32 {
    if let Ok(stage) = load_stage(path) {
        stage.ingest_seq + 1
    } else {
        1
    }
}
