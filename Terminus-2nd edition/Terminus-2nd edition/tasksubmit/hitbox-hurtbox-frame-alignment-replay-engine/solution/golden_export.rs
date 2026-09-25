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
    let manifest = ledger::read_manifest(manifest_path)?;
    ledger::validate_for_export(&manifest, ledger_path, entities_path, animation_path)?;
    export_from_ledger(ledger_path, manifest.tick_rate, manifest.anim_fps)
}

pub fn finalize_report(mut report: CollisionReport) -> CollisionReport {
    report.hits.sort_by(|a, b| {
        (
            a.tick,
            a.defender_id.as_str(),
            a.instance_id,
            a.attacker_id.as_str(),
        )
            .cmp(&(
                b.tick,
                b.defender_id.as_str(),
                b.instance_id,
                b.attacker_id.as_str(),
            ))
    });
    report.events.sort_by(|a, b| {
        (a.tick, a.entity_id.as_str()).cmp(&(b.tick, b.entity_id.as_str()))
    });
    report
}

pub fn push_hit(report: &mut CollisionReport, hit: HitEvent) {
    report.hits.push(hit);
}

pub fn push_event(report: &mut CollisionReport, event: ReplayEvent) {
    report.events.push(event);
}
