use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

pub type EntityId = u32;
pub type ComponentId = u16;

#[derive(Debug, Clone, Deserialize)]
pub struct ComponentSpec {
    pub size: u32,
    pub align: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(untagged)]
pub enum ComponentData {
    Hex(String),
    Detailed {
        data: String,
        #[serde(default)]
        align: Option<u32>,
    },
}

impl ComponentData {
    pub fn data(&self) -> &str {
        match self {
            ComponentData::Hex(s) => s,
            ComponentData::Detailed { data, .. } => data,
        }
    }

    pub fn align_override(&self) -> Option<u32> {
        match self {
            ComponentData::Hex(_) => None,
            ComponentData::Detailed { align, .. } => *align,
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct EntitySpec {
    pub id: EntityId,
    pub components: BTreeMap<String, ComponentData>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum JournalOp {
    AddComponent {
        entity: EntityId,
        component: String,
        data: String,
        #[serde(default)]
        align: Option<u32>,
    },
    RemoveComponent {
        entity: EntityId,
        component: String,
    },
    RemoveEntity {
        entity: EntityId,
    },
    Tombstone {
        entity: EntityId,
    },
    Spawn {
        entity: EntityId,
        components: BTreeMap<String, ComponentData>,
    },
}

#[derive(Debug, Clone, Deserialize)]
pub struct QuerySpec {
    pub component_ids: Vec<ComponentId>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct WorldSpec {
    pub component_names: Vec<String>,
    pub components: BTreeMap<String, ComponentSpec>,
    pub entities: Vec<EntitySpec>,
    pub journal: Vec<JournalOp>,
    #[serde(default)]
    pub queries: Vec<QuerySpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchetypeOut {
    pub hash: String,
    pub component_ids: Vec<ComponentId>,
    pub alignments: Vec<u32>,
    pub count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityOut {
    pub id: EntityId,
    pub archetype_hash: String,
    pub slot_generation: u32,
    pub components: BTreeMap<ComponentId, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MigrateExport {
    pub seed: String,
    pub generation: u64,
    pub component_map: BTreeMap<String, ComponentId>,
    pub archetypes: Vec<ArchetypeOut>,
    pub entities: Vec<EntityOut>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MigrateSnapshot {
    pub snapshot_version: u32,
    pub seed: String,
    pub generation: u64,
    pub component_map: BTreeMap<String, ComponentId>,
    pub archetypes: Vec<ArchetypeOut>,
    pub entities: Vec<EntityOut>,
}

impl From<MigrateExport> for MigrateSnapshot {
    fn from(doc: MigrateExport) -> Self {
        Self {
            snapshot_version: 1,
            seed: doc.seed,
            generation: doc.generation,
            component_map: doc.component_map,
            archetypes: doc.archetypes,
            entities: doc.entities,
        }
    }
}

impl From<MigrateSnapshot> for MigrateExport {
    fn from(snap: MigrateSnapshot) -> Self {
        Self {
            seed: snap.seed,
            generation: snap.generation,
            component_map: snap.component_map,
            archetypes: snap.archetypes,
            entities: snap.entities,
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct QueryExport {
    pub seed: String,
    pub generation: u64,
    pub query: Vec<ComponentId>,
    pub entities: Vec<EntityId>,
    pub cache_hit: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct QueryBatchStep {
    pub world_path: String,
    pub components: Vec<ComponentId>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct QueryBatchSpec {
    pub steps: Vec<QueryBatchStep>,
}

#[derive(Debug, Clone, Serialize)]
pub struct QueryBatchExport {
    pub seed: String,
    pub results: Vec<QueryExport>,
}
