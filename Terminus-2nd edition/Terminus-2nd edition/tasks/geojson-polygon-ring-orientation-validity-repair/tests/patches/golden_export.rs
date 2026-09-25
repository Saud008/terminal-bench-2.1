use std::fs;
use std::path::Path;

use anyhow::Result;

use crate::staging::{load_repair_snapshot, snapshot_repair_binding, verify_ledger_head};
use crate::types::{FixtureReport, RepairReport, RepairStats};

pub fn write_report(
    path: &Path,
    valid: bool,
    _fixtures: Vec<FixtureReport>,
    _stats: RepairStats,
) -> Result<()> {
    let snapshot = load_repair_snapshot()?;
    verify_ledger_head(&snapshot)?;
    let binding = snapshot_repair_binding(&snapshot)?;
    let report = RepairReport {
        report_version: 1,
        valid: valid && !snapshot.fixtures.is_empty(),
        fixtures: snapshot.fixtures,
        stats: snapshot.stats,
        repair_binding: binding,
    };
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(&report)? + "\n")?;
    Ok(())
}
