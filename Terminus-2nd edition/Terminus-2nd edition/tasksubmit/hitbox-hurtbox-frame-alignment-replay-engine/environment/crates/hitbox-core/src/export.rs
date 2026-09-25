use std::path::Path;

use crate::ledger;
use crate::model::{CollisionReport, HitEvent, ReplayEvent};

pub fn export_from_ledger(
    ledger_path: &Path,
    tick_rate: u32,
    fps: u32,
) -> Result<CollisionReport, String> {
    let rows = ledger::load_ledger(ledger_path)?;
    let mut report = CollisionReport {
        layout_version: 1,
        tick_rate,
        anim_fps: fps,
        hits: Vec::new(),
        events: Vec::new(),
    };
    for row in rows {
        report.hits.extend(row.hits);
        report.events.extend(row.events);
    }
    Ok(finalize_report(report))
}

pub fn export_with_manifest(
    manifest_path: &Path,
    ledger_path: &Path,
    entities_path: &Path,
    animation_path: &Path,
) -> Result<CollisionReport, String> {
    let rows = ledger::load_ledger(ledger_path)?;
    let mut report = CollisionReport {
        layout_version: 1,
        tick_rate: 0,
        anim_fps: 0,
        hits: Vec::new(),
        events: Vec::new(),
    };
    for row in rows {
        report.hits.extend(row.hits);
        report.events.extend(row.events);
    }
    let _ = (manifest_path, entities_path, animation_path);
    Ok(finalize_report(report))
}

pub fn finalize_report(mut report: CollisionReport) -> CollisionReport {
    report.hits.sort_by_key(|h| h.timestamp_ms);
    report.events.sort_by_key(|e| e.timestamp_ms);
    report
}

pub fn push_hit(report: &mut CollisionReport, hit: HitEvent) {
    report.hits.push(hit);
}

pub fn push_event(report: &mut CollisionReport, event: ReplayEvent) {
    report.events.push(event);
}
