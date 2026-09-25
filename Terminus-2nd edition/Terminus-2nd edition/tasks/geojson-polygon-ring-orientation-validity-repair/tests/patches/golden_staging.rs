use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::types::{FixtureReport, RepairSnapshot, RepairStats};

pub const SNAPSHOT_PATH: &str = "/app/state/repair-snapshot.json";
pub const LEDGER_PATH: &str = "/app/state/repair-ledger.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SnapshotDigestBody {
    fixtures: Vec<FixtureReport>,
    stats: RepairStats,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct LedgerEntry {
    sequence: u32,
    fixture_count: u32,
    snapshot_digest: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
struct RepairLedger {
    entries: Vec<LedgerEntry>,
}

fn sorted_fixtures(mut fixtures: Vec<FixtureReport>) -> Vec<FixtureReport> {
    fixtures.sort_by(|a, b| a.name.cmp(&b.name));
    fixtures
}

fn snapshot_digest(fixtures: &[FixtureReport], stats: &RepairStats) -> Result<String> {
    let body = SnapshotDigestBody {
        fixtures: fixtures.to_vec(),
        stats: stats.clone(),
    };
    let data = serde_json::to_vec(&body)?;
    Ok(format!("{:x}", Sha256::digest(&data)))
}

fn repair_binding_from_digest(digest: &str) -> String {
    let payload = format!("repair\n{digest}");
    format!("{:x}", Sha256::digest(payload.as_bytes()))
}

fn next_sequence(ledger: &RepairLedger) -> u32 {
    ledger
        .entries
        .last()
        .map(|entry| entry.sequence + 1)
        .unwrap_or(1)
}

pub fn persist_repair_snapshot(fixtures: &[FixtureReport], stats: &RepairStats) -> Result<()> {
    let fixtures = sorted_fixtures(fixtures.to_vec());
    let digest = snapshot_digest(&fixtures, stats)?;
    let mut ledger = RepairLedger::default();
    if let Ok(data) = fs::read_to_string(LEDGER_PATH) {
        if let Ok(parsed) = serde_json::from_str::<RepairLedger>(&data) {
            ledger = parsed;
        }
    }
    let sequence = next_sequence(&ledger);
    let snapshot = RepairSnapshot {
        sequence,
        fixtures,
        stats: stats.clone(),
    };
    fs::create_dir_all(Path::new(SNAPSHOT_PATH).parent().unwrap())?;
    fs::write(
        SNAPSHOT_PATH,
        serde_json::to_string_pretty(&snapshot)? + "\n",
    )?;
    ledger.entries.push(LedgerEntry {
        sequence,
        fixture_count: snapshot.fixtures.len() as u32,
        snapshot_digest: digest,
    });
    fs::write(LEDGER_PATH, serde_json::to_string_pretty(&ledger)? + "\n")?;
    Ok(())
}

pub fn load_repair_snapshot() -> Result<RepairSnapshot> {
    let data = fs::read_to_string(SNAPSHOT_PATH)
        .with_context(|| format!("missing repair snapshot at {SNAPSHOT_PATH}"))?;
    serde_json::from_str(&data).context("malformed repair snapshot")
}

pub fn verify_ledger_head(snapshot: &RepairSnapshot) -> Result<()> {
    let data = fs::read_to_string(LEDGER_PATH)
        .with_context(|| format!("missing repair ledger at {LEDGER_PATH}"))?;
    let ledger: RepairLedger = serde_json::from_str(&data).context("malformed repair ledger")?;
    let head = ledger
        .entries
        .last()
        .context("repair ledger head missing")?;
    let digest = snapshot_digest(&snapshot.fixtures, &snapshot.stats)?;
    if head.sequence != snapshot.sequence
        || head.fixture_count != snapshot.fixtures.len() as u32
        || head.snapshot_digest != digest
    {
        anyhow::bail!("repair ledger head does not match snapshot");
    }
    Ok(())
}

pub fn snapshot_repair_binding(snapshot: &RepairSnapshot) -> Result<String> {
    let digest = snapshot_digest(&snapshot.fixtures, &snapshot.stats)?;
    Ok(repair_binding_from_digest(&digest))
}
