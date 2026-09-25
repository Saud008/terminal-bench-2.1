use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestFile {
    pub mismatch_budget: u32,
    pub umi_length: usize,
    pub barcode_length: usize,
    pub precedence_order: String,
    pub samples: Vec<SampleBarcode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanesFile {
    pub precedence_order: String,
    pub lanes: Vec<LaneConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LaneConfig {
    pub lane_id: String,
    pub seed_shift: u32,
    pub overrides: Vec<SampleBarcode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SampleBarcode {
    pub sample_id: String,
    pub barcode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedPair {
    pub pair_id: String,
    pub lane_id: String,
    pub r1_barcode: String,
    pub r1_umi: String,
    pub r2_umi: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingFile {
    pub ingest_seq: u32,
    pub precedence_order: String,
    pub mismatch_budget: u32,
    pub umi_length: usize,
    pub barcode_length: usize,
    pub samples_global: Vec<SampleBarcode>,
    pub lanes: Vec<LaneConfig>,
    pub pairs: Vec<StagedPair>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DemuxEntry {
    pub pair_id: String,
    pub lane_id: String,
    pub sample_id: String,
    pub r1_canonical: String,
    pub r2_canonical: String,
    pub canonical_umi: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollisionCluster {
    pub cluster_id: String,
    pub sample_id: String,
    pub canonical_umi: String,
    pub pair_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerFile {
    pub demux_seq: u32,
    pub ingest_seq: u32,
    pub entries: Vec<DemuxEntry>,
    pub clusters: Vec<CollisionCluster>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContaminationFlag {
    pub canonical_umi: String,
    pub sample_ids: Vec<String>,
    pub flag: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasFile {
    pub atlas_version: u32,
    pub ingest_seq: u32,
    pub demux_seq: u32,
    pub clusters: Vec<CollisionCluster>,
    pub contamination_flags: Vec<ContaminationFlag>,
}
