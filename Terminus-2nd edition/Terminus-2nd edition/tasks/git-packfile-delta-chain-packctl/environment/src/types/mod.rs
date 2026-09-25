use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CatalogEntry {
    pub id: String,
    pub kind: String,
    pub pack_offset: u64,
    pub compressed_size: u64,
    #[serde(default)]
    pub base_id: Option<String>,
    #[serde(default)]
    pub base_pack_offset: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackCatalog {
    pub pack_id: String,
    pub entries: Vec<CatalogEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StageObject {
    pub id: String,
    pub kind: String,
    pub pack_offset: u64,
    pub compressed_size: u64,
    #[serde(default)]
    pub base_id: Option<String>,
    #[serde(default)]
    pub base_pack_offset: Option<u64>,
    pub catalog_order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackStage {
    pub pack_id: String,
    pub ingest_seq: u32,
    pub pack_stream_path: String,
    pub objects: Vec<StageObject>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportObject {
    pub id: String,
    pub kind: String,
    pub inflated_size: u64,
    pub sha1: String,
    pub chain_depth: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackExport {
    pub pack_id: String,
    pub objects: Vec<ExportObject>,
    pub total_inflated_bytes: u64,
}

pub const KIND_BLOB: &str = "blob";
pub const KIND_TREE: &str = "tree";
pub const KIND_OFS_DELTA: &str = "ofs_delta";
pub const KIND_REF_DELTA: &str = "ref_delta";

pub fn allowed_delta_base(kind: &str) -> bool {
    !matches!(kind, "commit" | "tag")
}
