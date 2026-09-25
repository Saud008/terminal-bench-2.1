use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    pub sketch_index_dir: String,
    pub cluster_graph_dir: String,
    pub corpus_root: String,
    pub shingle_k: usize,
    pub num_hashes: usize,
    pub base_seed: u64,
    pub default_jaccard_floor: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorpusDoc {
    pub doc_id: String,
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SketchDoc {
    pub doc_id: String,
    pub source_path: String,
    pub token_count: u32,
    pub shingle_count: u32,
    pub signature: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SketchIndex {
    pub run_id: String,
    pub profile: String,
    pub scan_generation: u32,
    pub config_fingerprint: String,
    pub shingle_k: u32,
    pub num_hashes: u32,
    pub base_seed: u64,
    pub documents: Vec<SketchDoc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClusterRecord {
    pub cluster_id: String,
    pub representative_doc_id: String,
    pub member_doc_ids: Vec<String>,
    pub min_pairwise_estimate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClusterGraph {
    pub run_id: String,
    pub jaccard_floor: f64,
    pub group_generation: u32,
    pub cluster_run_id: String,
    pub clusters: Vec<ClusterRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceCluster {
    pub cluster_id: String,
    pub representative_doc_id: String,
    pub member_doc_ids: Vec<String>,
    pub source_paths: Vec<String>,
    pub min_pairwise_estimate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceReport {
    pub run_id: String,
    pub cluster_run_id: String,
    pub jaccard_floor: f64,
    pub total_documents: u32,
    pub cluster_count: u32,
    pub singleton_count: u32,
    pub clusters: Vec<ProvenanceCluster>,
    pub audit_digest: String,
}
