use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    pub sample_matrix_dir: String,
    pub block_edge_list_dir: String,
    pub fixture_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestSample {
    pub sample_id: String,
    pub lineage_rank: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub profile: String,
    pub samples: Vec<ManifestSample>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedGenotype {
    pub sample_id: String,
    pub gt_raw: String,
    pub phased: bool,
    pub missing: bool,
    pub alleles: Vec<u32>,
    pub ps_tag: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VariantRecord {
    pub chrom: String,
    pub pos: u32,
    pub ref_allele: String,
    pub alt_alleles: Vec<String>,
    pub genotypes: Vec<ParsedGenotype>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SamplePhaseMatrix {
    pub run_id: String,
    pub profile: String,
    pub ingest_generation: u32,
    pub sample_lineage: Vec<String>,
    pub variant_catalog: Vec<VariantRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockAnomaly {
    pub anomaly_id: String,
    pub chrom: String,
    pub ps_tag: String,
    pub anomaly_type: String,
    pub sample_ids: Vec<String>,
    pub variant_positions: Vec<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhasedBlock {
    pub block_id: String,
    pub chrom: String,
    pub ps_tag: String,
    pub variant_count: u32,
    pub sample_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsistencyReport {
    pub run_id: String,
    pub block_count: u32,
    pub anomaly_count: u32,
    pub blocks: Vec<PhasedBlock>,
    pub anomalies: Vec<BlockAnomaly>,
    pub audit_digest: String,
}
