use std::collections::BTreeMap;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use crate::duplicate;
use crate::envelope;
use crate::export;
use crate::idempotent;
use crate::model::{
    AuditEntry, GenerationFile, PityLedgerFile, PlayerLedger, ProcessedEventsFile, PullEvent,
    SeasonConfig, SettlementReport, StagingSnapshot,
};
use crate::pity;
use crate::pool;
use crate::staging;

pub const STAGING_PATH: &str = "/app/state/settlement-staging.json";
pub const PITY_LEDGER_PATH: &str = "/app/state/pity-ledger.json";
pub const PROCESSED_PATH: &str = "/app/state/processed-events.json";
pub const GENERATION_PATH: &str = "/app/state/replay-generation.json";
pub const STAGING_SEQ_PATH: &str = "/app/state/staging-seq.json";
pub const AUDIT_CACHE_PATH: &str = "/app/state/settlement-audit.json";

pub fn load_season(path: &Path) -> Result<SeasonConfig, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn load_season_by_id(seasons_dir: &Path, season_id: &str) -> Result<SeasonConfig, String> {
    for entry in fs::read_dir(seasons_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }
        let season = load_season(&path)?;
        if season.season_id == season_id {
            return Ok(season);
        }
    }
    Err(format!("season not found: {season_id}"))
}

pub fn load_events_jsonl(path: &Path) -> Result<Vec<PullEvent>, String> {
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

fn next_staging_generation() -> Result<u64, String> {
    let path = Path::new(STAGING_SEQ_PATH);
    let current = if path.is_file() {
        let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
        serde_json::from_str::<serde_json::Value>(&raw)
            .ok()
            .and_then(|v| v.get("staging_generation").and_then(|g| g.as_u64()))
            .unwrap_or(0)
    } else {
        0
    };
    let next = current + 1;
    fs::write(
        path,
        serde_json::json!({ "staging_generation": next }).to_string(),
    )
    .map_err(|e| e.to_string())?;
    Ok(next)
}

pub fn run_ingest(season_path: &Path, events_path: &Path) -> Result<(), String> {
    let season = load_season(season_path)?;
    let events = load_events_jsonl(events_path)?;
    let mut validated = Vec::new();
    for event in events {
        let value = serde_json::to_value(&event).map_err(|e| e.to_string())?;
        let event_season = load_season_by_id(
            season_path
                .parent()
                .ok_or_else(|| "season path has no parent".to_string())?,
            &event.season_id,
        )?;
        envelope::verify_event_signature(&value, &event_season.hmac_secret)?;
        pool::validate_pool_epoch(event.pool_epoch, &event_season)?;
        validated.push(event);
    }
    let staging_generation = next_staging_generation()?;
    let staging = staging::build_staging(
        validated,
        season.season_id.clone(),
        season.pool_epoch,
        staging_generation,
    )?;
    write_json(Path::new(STAGING_PATH), &staging)
}

fn write_json<T: serde::Serialize>(path: &Path, value: &T) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, raw).map_err(|e| e.to_string())
}

fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn run_settle(seasons_dir: &Path) -> Result<(), String> {
    let staging: StagingSnapshot = read_json(Path::new(STAGING_PATH))?;
    staging::verify_staging_digest(&staging)?;
    let mut ledger: PityLedgerFile = read_json(Path::new(PITY_LEDGER_PATH)).unwrap_or(PityLedgerFile {
        players: BTreeMap::new(),
    });
    let mut processed: ProcessedEventsFile =
        read_json(Path::new(PROCESSED_PATH)).unwrap_or(ProcessedEventsFile {
            event_ids: Vec::new(),
        });
    let mut audit_log: Vec<AuditEntry> = Vec::new();
    let ordered = staging::sort_events(&staging.events);
    for event in ordered {
        if idempotent::already_processed(&processed, &event.event_id) {
            audit_log.push(idempotent::duplicate_skip_audit(
                &event.event_id,
                &event.player_id,
                &event.season_id,
                &event.item_id,
                &event.rarity,
                event.seq,
                event.timestamp_ms,
            ));
            continue;
        }
        let new_season = load_season_by_id(seasons_dir, &event.season_id)?;
        pool::validate_pool_epoch(event.pool_epoch, &new_season)?;
        let value = serde_json::to_value(&event).map_err(|e| e.to_string())?;
        envelope::verify_event_signature(&value, &new_season.hmac_secret)?;
        let player = ledger
            .players
            .entry(event.player_id.clone())
            .or_insert_with(|| PlayerLedger {
                season_id: event.season_id.clone(),
                inventory: Vec::new(),
                shards: 0,
                pity_legendary: 0,
            });
        if player.season_id != event.season_id {
            let old_season = load_season_by_id(seasons_dir, &player.season_id)?;
            pity::apply_season_carryover(player, &old_season, &new_season);
        }
        let mut entry = duplicate::process_grant(
            player,
            &new_season,
            &event.event_id,
            &event.item_id,
            &event.rarity,
            event.seq,
            event.timestamp_ms,
        );
        entry.player_id = event.player_id.clone();
        audit_log.push(entry);
        pity::apply_pity_after_pull(player, &event.rarity);
        player.season_id = event.season_id.clone();
        idempotent::record_processed(&mut processed, &event.event_id);
    }
    let mut generation: GenerationFile = read_json(Path::new(GENERATION_PATH)).unwrap_or(GenerationFile {
        generation: 0,
    });
    generation.generation = generation.generation.saturating_add(1);
    write_json(Path::new(PITY_LEDGER_PATH), &ledger)?;
    write_json(Path::new(PROCESSED_PATH), &processed)?;
    write_json(Path::new(GENERATION_PATH), &generation)?;
    write_json(Path::new(AUDIT_CACHE_PATH), &audit_log)?;
    Ok(())
}

pub fn run_export(output_path: &Path) -> Result<SettlementReport, String> {
    let staging: StagingSnapshot = read_json(Path::new(STAGING_PATH))?;
    let ledger: PityLedgerFile = read_json(Path::new(PITY_LEDGER_PATH))?;
    let generation: GenerationFile = read_json(Path::new(GENERATION_PATH))?;
    let audit_log: Vec<AuditEntry> = read_json(Path::new(AUDIT_CACHE_PATH)).unwrap_or_default();
    export::build_report(&staging, &ledger, &generation, audit_log)
}

pub fn run_replay(
    season_path: &Path,
    events_path: &Path,
    seasons_dir: &Path,
    output_path: &Path,
) -> Result<SettlementReport, String> {
    run_ingest(season_path, events_path)?;
    run_settle(seasons_dir)?;
    let report = run_export(output_path)?;
    write_report(output_path, &report)?;
    Ok(report)
}

pub fn write_report(path: &Path, report: &SettlementReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = export::sorted_report_json(report)?;
    fs::write(path, raw).map_err(|e| e.to_string())
}
