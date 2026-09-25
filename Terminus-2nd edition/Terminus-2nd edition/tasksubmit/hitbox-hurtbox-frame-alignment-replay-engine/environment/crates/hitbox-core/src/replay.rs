use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use crate::collision::{detect_hits, load_pose_map};
use crate::export::export_with_manifest;
use crate::ledger::{self, MANIFEST_PATH};
use crate::model::{CollisionReport, EntitiesFile, KeyframeRecord};

const LEDGER_PATH: &str = "/app/state/tick-ledger.jsonl";

pub fn load_entities(path: &Path) -> Result<EntitiesFile, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn load_keyframes(path: &Path) -> Result<Vec<KeyframeRecord>, String> {
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);
    let mut out = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        out.push(serde_json::from_str(trimmed).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn run_sample(
    entities_path: &Path,
    animation_path: &Path,
    tick_rate: u32,
    fps: u32,
    max_tick: u32,
) -> Result<(), String> {
    let entities = load_entities(entities_path)?;
    let keyframes = load_keyframes(animation_path)?;
    let pose_map = load_pose_map(&keyframes);
    let ledger_path = PathBuf::from(LEDGER_PATH);
    let manifest_path = PathBuf::from(MANIFEST_PATH);
    let epoch = ledger::load_next_epoch()?;

    ledger::reset_ledger(&ledger_path)?;

    for tick in 0..=max_tick {
        let (hits, events) = detect_hits(&entities, &pose_map, tick, tick_rate, fps);
        ledger::append_tick(&ledger_path, tick, &hits, &events)?;
    }

    ledger::finalize_manifest(
        &manifest_path,
        &ledger_path,
        entities_path,
        animation_path,
        tick_rate,
        fps,
        max_tick,
        epoch,
    )?;
    ledger::persist_epoch(epoch)?;
    Ok(())
}

pub fn run_export(
    entities_path: &Path,
    animation_path: &Path,
) -> Result<CollisionReport, String> {
    let ledger_path = PathBuf::from(LEDGER_PATH);
    let manifest_path = PathBuf::from(MANIFEST_PATH);
    export_with_manifest(
        &manifest_path,
        &ledger_path,
        entities_path,
        animation_path,
    )
}

pub fn run_replay(
    entities_path: &Path,
    animation_path: &Path,
    tick_rate: u32,
    fps: u32,
    max_tick: u32,
) -> Result<CollisionReport, String> {
    run_sample(entities_path, animation_path, tick_rate, fps, max_tick)?;
    run_export(entities_path, animation_path)
}

pub fn write_report(path: &Path, report: &CollisionReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, raw).map_err(|e| e.to_string())
}
