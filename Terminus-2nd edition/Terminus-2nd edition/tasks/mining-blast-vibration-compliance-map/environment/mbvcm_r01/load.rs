use crate::survey_root;
use crate::types::SurveyRecord;
use std::fs;
use std::path::{Path, PathBuf};

pub fn survey_path(name: &str) -> PathBuf {
    let root = survey_root();
    Path::new(&root).join(format!("{name}.json"))
}

pub fn load_survey(path: &Path) -> Result<SurveyRecord, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
