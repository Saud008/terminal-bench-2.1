//! Compile-time public API contract for ecs-core.
//!
//! Signature drift fails `cargo test -p ecs-core api_contract` at compile time.

use std::path::Path;

use anyhow::Result;
use ecs_core::archetype::rebuild_archetype_table;
use ecs_core::checksum::{chunk_checksum, decode_chunk};
use ecs_core::entity_id::{remap_new_entity_ids, tombstone_ids};
use ecs_core::journal::{load_journal, mark_committed, replay_start_cursor};
use ecs_core::migrator::{apply_steps, ordered_steps};
use ecs_core::model::{LayoutManifest, MigrationStep, ReplayJournal};
use rusqlite::Connection;

const _: fn(&LayoutManifest) -> Vec<MigrationStep> = ordered_steps;

const _: fn(
    &Connection,
    &Path,
    &LayoutManifest,
    u32,
) -> Result<(Vec<(u32, String, String, u32)>, u32)> = apply_steps;

const _: fn(&Connection, &LayoutManifest, &Path) -> Result<()> = rebuild_archetype_table;

const _: fn(&Connection) -> Result<u32> = remap_new_entity_ids;
const _: fn(&Connection) -> Result<Vec<u32>> = tombstone_ids;

const _: fn(&Path) -> Result<ReplayJournal> = load_journal;
const _: fn(&ReplayJournal) -> u32 = replay_start_cursor;
const _: fn(&Path, &ReplayJournal) -> Result<()> = mark_committed;

const _: fn(u32, u32, &[u8]) -> String = chunk_checksum;
const _: fn(&[u8]) -> anyhow::Result<(u32, u32, Vec<u8>)> = decode_chunk;

#[test]
fn api_contract_public_signatures() {
    // Compile-time checks above enforce the module-contracts.md surface.
}
