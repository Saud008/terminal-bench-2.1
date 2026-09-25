use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde::Deserialize;

use crate::error::SlError;

pub fn polarity_config_root() -> PathBuf {
    if let Ok(root) = std::env::var("TB3_POLARITY_ROOT") {
        if !root.is_empty() {
            return PathBuf::from(root);
        }
    }
    PathBuf::from("/app/config/polarity")
}

pub fn load_polarity_sheet(network: &str, root: Option<&Path>) -> Result<HashMap<String, i8>, SlError> {
    let base = root.map(Path::to_path_buf).unwrap_or_else(polarity_config_root);
    let path = base.join(format!("{network}.pol"));
    if !path.is_file() {
        return Ok(HashMap::new());
    }
    let text = fs::read_to_string(path)?;
    let raw: HashMap<String, i32> = serde_json::from_str(&text)?;
    Ok(raw.into_iter().map(|(k, v)| (k, v as i8)).collect())
}

pub fn effective_polarity(
    _network: &str,
    _station: &str,
    body_polarity: i8,
    _root: Option<&Path>,
) -> Result<i8, SlError> {
    Ok(body_polarity)
}
