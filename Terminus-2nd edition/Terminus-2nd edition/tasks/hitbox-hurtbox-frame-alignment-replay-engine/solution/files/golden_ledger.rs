use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

use crate::model::{HitEvent, ReplayEvent};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const MANIFEST_PATH: &str = "/app/state/replay-manifest.json";
pub const SEQ_PATH: &str = "/app/state/replay-seq.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct LedgerHeader {
    #[serde(rename = "_kind")]
    pub kind: String,
    pub epoch: u64,
    pub row_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReplayManifest {
    pub epoch: u64,
    pub entities_sha256: String,
    pub animation_sha256: String,
    pub tick_rate: u32,
    pub anim_fps: u32,
    pub max_tick: u32,
    pub row_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TickLedgerRow {
    pub tick: u32,
    pub hits: Vec<HitEvent>,
    pub events: Vec<ReplayEvent>,
}

pub fn sha256_file(path: &Path) -> Result<String, String> {
    let bytes = fs::read(path).map_err(|e| e.to_string())?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn load_next_epoch() -> Result<u64, String> {
    let path = Path::new(SEQ_PATH);
    if !path.is_file() {
        return Ok(1);
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let value: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    Ok(value
        .get("epoch")
        .and_then(|v| v.as_u64())
        .unwrap_or(0)
        .saturating_add(1))
}

pub fn persist_epoch(epoch: u64) -> Result<(), String> {
    if let Some(parent) = Path::new(SEQ_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let payload = serde_json::json!({ "epoch": epoch });
    fs::write(SEQ_PATH, payload.to_string()).map_err(|e| e.to_string())
}

pub fn reset_ledger(path: &Path) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(path, "").map_err(|e| e.to_string())
}

pub fn write_ledger_header(path: &Path, epoch: u64, row_count: u32) -> Result<(), String> {
    let header = LedgerHeader {
        kind: "header".to_string(),
        epoch,
        row_count,
    };
    let line = serde_json::to_string(&header).map_err(|e| e.to_string())?;
    fs::write(path, format!("{line}\n")).map_err(|e| e.to_string())
}

pub fn write_manifest(
    manifest_path: &Path,
    entities_path: &Path,
    animation_path: &Path,
    tick_rate: u32,
    fps: u32,
    max_tick: u32,
    epoch: u64,
    row_count: u32,
) -> Result<ReplayManifest, String> {
    let manifest = ReplayManifest {
        epoch,
        entities_sha256: sha256_file(entities_path)?,
        animation_sha256: sha256_file(animation_path)?,
        tick_rate,
        anim_fps: fps,
        max_tick,
        row_count,
    };
    if let Some(parent) = manifest_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(&manifest).map_err(|e| e.to_string())?;
    fs::write(manifest_path, raw).map_err(|e| e.to_string())?;
    Ok(manifest)
}

pub fn validate_for_export(
    manifest: &ReplayManifest,
    ledger_path: &Path,
    entities_path: &Path,
    animation_path: &Path,
) -> Result<(), String> {
    let header = read_ledger_header(ledger_path)?;
    if header.epoch != manifest.epoch {
        return Err("ledger epoch mismatch".to_string());
    }
    if header.row_count != manifest.row_count {
        return Err("ledger row_count mismatch".to_string());
    }
    let rows = load_ledger(ledger_path)?;
    if rows.len() as u32 != manifest.row_count {
        return Err("ledger row count drift".to_string());
    }
    let entities_sha = sha256_file(entities_path)?;
    let animation_sha = sha256_file(animation_path)?;
    if manifest.entities_sha256 != entities_sha {
        return Err("entities sha256 mismatch".to_string());
    }
    if manifest.animation_sha256 != animation_sha {
        return Err("animation sha256 mismatch".to_string());
    }
    Ok(())
}

pub fn read_manifest(path: &Path) -> Result<ReplayManifest, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn read_ledger_header(path: &Path) -> Result<LedgerHeader, String> {
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let mut lines = BufReader::new(file).lines();
    let first = lines
        .next()
        .ok_or_else(|| "ledger empty".to_string())?
        .map_err(|e| e.to_string())?;
    serde_json::from_str(first.trim()).map_err(|e| e.to_string())
}

pub fn append_tick(
    path: &Path,
    tick: u32,
    hits: &[HitEvent],
    events: &[ReplayEvent],
) -> Result<(), String> {
    let row = TickLedgerRow {
        tick,
        hits: hits.to_vec(),
        events: events.to_vec(),
    };
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    let line = serde_json::to_string(&row).map_err(|e| e.to_string())?;
    writeln!(file, "{line}").map_err(|e| e.to_string())
}

pub fn load_ledger(path: &Path) -> Result<Vec<TickLedgerRow>, String> {
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);
    let mut rows = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        if let Ok(header) = serde_json::from_str::<LedgerHeader>(trimmed) {
            if header.kind == "header" {
                continue;
            }
        }
        rows.push(serde_json::from_str(trimmed).map_err(|e| e.to_string())?);
    }
    Ok(rows)
}

pub fn finalize_manifest(
    manifest_path: &Path,
    ledger_path: &Path,
    entities_path: &Path,
    animation_path: &Path,
    tick_rate: u32,
    fps: u32,
    max_tick: u32,
    epoch: u64,
) -> Result<ReplayManifest, String> {
    let rows = load_ledger(ledger_path)?;
    let row_count = rows.len() as u32;
    let header = LedgerHeader {
        kind: "header".to_string(),
        epoch,
        row_count,
    };
    let header_line = serde_json::to_string(&header).map_err(|e| e.to_string())?;
    let mut body = String::new();
    for row in &rows {
        let line = serde_json::to_string(row).map_err(|e| e.to_string())?;
        body.push_str(&line);
        body.push('\n');
    }
    fs::write(ledger_path, format!("{header_line}\n{body}")).map_err(|e| e.to_string())?;
    write_manifest(
        manifest_path,
        entities_path,
        animation_path,
        tick_rate,
        fps,
        max_tick,
        epoch,
        row_count,
    )
}
