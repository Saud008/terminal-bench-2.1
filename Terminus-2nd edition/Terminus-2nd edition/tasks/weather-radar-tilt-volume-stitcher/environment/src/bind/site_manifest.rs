use crate::models::ScanBundle;
use std::path::PathBuf;

pub fn site_bind_path(token: &str) -> PathBuf {
    PathBuf::from(format!("{}/site-bind-{}.json", crate::VAR_ROOT, token))
}

pub fn write_site_bind(token: &str, bundle: &ScanBundle) -> Result<(), String> {
    let body = serde_json::to_string_pretty(bundle).map_err(|e| e.to_string())?;
    std::fs::write(site_bind_path(token), body).map_err(|e| e.to_string())
}
