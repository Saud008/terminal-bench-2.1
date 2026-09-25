use crate::error::{Result, XanesError};
use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct WindowNode {
    pub window_id: String,
    pub element: String,
    pub atomic_number: u32,
    pub edge_code: String,
    pub e_lo: f64,
    pub e_hi: f64,
    #[serde(default)]
    pub channels: Vec<String>,
    #[serde(default)]
    pub children: Vec<WindowNode>,
}

#[derive(Debug, Deserialize)]
pub struct WindowsFile {
    pub windows: Vec<WindowNode>,
}

/// Bind nested fluorescence window scopes from JSON.
pub fn bind_windows(path: &Path) -> Result<Vec<WindowNode>> {
    let raw = fs::read_to_string(path)?;
    let file: WindowsFile = serde_json::from_str(&raw)?;
    if file.windows.is_empty() {
        return Err(XanesError::Msg("bind: empty windows".into()));
    }
    Ok(file.windows)
}

pub fn min_window_lo(windows: &[WindowNode]) -> f64 {
    windows
        .iter()
        .map(|w| w.e_lo)
        .fold(f64::INFINITY, f64::min)
}
