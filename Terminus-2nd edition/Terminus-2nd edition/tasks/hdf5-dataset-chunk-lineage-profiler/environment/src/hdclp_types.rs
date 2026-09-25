use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct CatalogFile {
    pub version: u32,
    pub root: String,
    pub datasets: Vec<DatasetSpec>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct DatasetSpec {
    pub path: String,
    pub dims: Vec<u64>,
    pub chunk_dims: Vec<u64>,
    pub filters: Vec<String>,
    pub fill_value: f64,
    #[serde(default)]
    pub mask_rel: Option<String>,
    pub attrs: BTreeMap<String, serde_json::Value>,
    #[serde(default)]
    pub parent_chain: Vec<ParentAttrs>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct ParentAttrs {
    pub path: String,
    pub attrs: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChunkRecord {
    pub dataset_path: String,
    pub chunk_index: u32,
    pub origin: Vec<u64>,
    pub filter_chain_id: u32,
    pub filter_chain_hash: String,
    pub payload_bytes: u32,
    pub masked_cells: u32,
    pub effective_attrs: BTreeMap<String, serde_json::Value>,
    pub coord_labels: Vec<f64>,
    pub coord_consistent: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StagingSnapshot {
    pub version: u32,
    pub catalog_root: String,
    pub sequence: u64,
    pub chunks: Vec<ChunkRecord>,
    pub compression_totals: CompressionTotals,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct CompressionTotals {
    pub total_payload_bytes: u64,
    pub total_masked_cells: u64,
    pub filter_usage: BTreeMap<String, u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct LineageReport {
    pub version: u32,
    pub sequence: u64,
    pub datasets: BTreeMap<String, DatasetLineage>,
    pub compression_summary: CompressionTotals,
    pub export_fingerprint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DatasetLineage {
    pub chunk_count: u32,
    pub chunks: Vec<ExportedChunk>,
    pub attribute_lineage: BTreeMap<String, serde_json::Value>,
    pub coordinate_ok: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportedChunk {
    pub chunk_index: u32,
    pub origin: Vec<u64>,
    pub filter_chain_hash: String,
    pub masked_cells: u32,
    pub coord_labels: Vec<f64>,
}

#[derive(Debug, Clone)]
pub struct IndexEntry {
    pub origin: Vec<u64>,
    pub filter_chain_id: u32,
    pub payload_bytes: u32,
    pub masked_cells: u32,
}

pub fn chunks_per_dim(dims: &[u64], chunk_dims: &[u64]) -> Vec<u64> {
    dims.iter()
        .zip(chunk_dims.iter())
        .map(|(d, c)| (*d + c - 1) / c)
        .collect()
}

pub fn total_chunks(dims: &[u64], chunk_dims: &[u64]) -> u32 {
    chunks_per_dim(dims, chunk_dims)
        .iter()
        .product::<u64>() as u32
}
