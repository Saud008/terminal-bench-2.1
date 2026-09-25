use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};

use crate::error::{CombatError, Result};
use crate::model::{RosterDoc, StagingDoc};

pub fn roster_checksum(actors: &[crate::model::Actor]) -> Result<String> {
    let payload = serde_json::to_string(actors).map_err(CombatError::Json)?;
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn ingest_roster(roster_path: &Path, staging_path: &Path) -> Result<StagingDoc> {
    let raw = fs::read_to_string(roster_path)?;
    let doc: RosterDoc = serde_json::from_str(&raw)?;
    if doc.actors.is_empty() {
        return Err(CombatError::InvalidRoster("empty roster".into()));
    }
    for actor in &doc.actors {
        if actor.hp <= 0 {
            return Err(CombatError::InvalidRoster("invalid hp".into()));
        }
    }
    let checksum = roster_checksum(&doc.actors)?;
    let staging = StagingDoc {
        staging_version: 1,
        rounds: doc.rounds,
        actors: doc.actors,
        checksum,
    };
    if let Some(parent) = staging_path.parent() {
        fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(&staging).map_err(CombatError::Json)?;
    fs::write(staging_path, format!("{json}\n"))?;
    Ok(staging)
}
