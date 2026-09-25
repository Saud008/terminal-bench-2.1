use std::fs;
use std::path::Path;

use anyhow::Result;

use crate::types::{FixtureReport, RepairReport, RepairStats};

pub fn write_report(
    path: &Path,
    valid: bool,
    mut fixtures: Vec<FixtureReport>,
    stats: RepairStats,
) -> Result<()> {
    fixtures.sort_by(|a, b| b.name.cmp(&a.name));
    let report = RepairReport {
        report_version: 1,
        valid: valid && !fixtures.is_empty(),
        fixtures,
        stats,
        repair_binding: String::new(),
    };
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(&report)? + "\n")?;
    Ok(())
}
