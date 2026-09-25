use serde::{Deserialize, Serialize};

pub const CHUNK_MAGIC: u32 = 0x4543_5331;

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq)]
pub struct ComponentSpec {
    pub name: String,
    pub offset: u32,
    pub size: u32,
    #[serde(default)]
    pub default_hex: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MigrationStep {
    pub order: u32,
    pub op: String,
    pub component: String,
    #[serde(default)]
    pub target_chunk: Option<u32>,
    #[serde(default)]
    pub from_archetype: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct LayoutManifest {
    pub layout_id: String,
    pub from_version: u32,
    pub to_version: u32,
    pub components: Vec<ComponentSpec>,
    pub migration_steps: Vec<MigrationStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportStep {
    pub order: u32,
    pub op: String,
    pub component: String,
    pub chunks_touched: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportArchetype {
    pub archetype_id: u32,
    pub signature: String,
    pub entity_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportChunk {
    pub chunk_id: u32,
    pub checksum: String,
    pub entity_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MigrationReport {
    pub layout_id: String,
    pub layout_version: u32,
    pub steps_applied: Vec<ReportStep>,
    pub archetypes: Vec<ReportArchetype>,
    pub chunks: Vec<ReportChunk>,
    pub entities_moved: u32,
    pub ids_remapped: u32,
    pub journal_replayed_from: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct JournalEntry {
    pub step_order: u32,
    pub chunk_id: u32,
    pub committed: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ReplayJournal {
    pub status: String,
    pub commit_cursor: u32,
    pub entries: Vec<JournalEntry>,
}

#[derive(Debug, Clone)]
pub struct EntityRow {
    pub stable_id: u32,
    pub archetype_id: u32,
    pub chunk_id: u32,
    pub slot: u32,
    pub alive: bool,
}

#[derive(Debug, Clone)]
pub struct ChunkEntity {
    pub stable_id: u32,
    pub payload: Vec<u8>,
}
