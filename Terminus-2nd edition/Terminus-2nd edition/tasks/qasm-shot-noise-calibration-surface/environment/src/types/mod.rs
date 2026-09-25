use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HistogramFile {
    pub qubits: Vec<String>,
    pub rows: Vec<HistogramRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HistogramRow {
    pub qubit: String,
    pub counts: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MitigationFile {
    pub candidates: Vec<MatrixCandidate>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatrixCandidate {
    pub id: String,
    pub dimension: usize,
    pub priority: i32,
    pub matrix: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeedManifest {
    pub seed_hash: String,
    pub experiment_id: String,
    pub calibration_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriftFile {
    pub factors: std::collections::HashMap<String, DriftFactor>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriftFactor {
    pub factor: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagingFile {
    pub ingest_seq: u32,
    pub manifest: SeedManifest,
    pub qasm_gate_count: u32,
    pub histogram: HistogramFile,
    pub mitigation: MitigationFile,
    pub drift: DriftFile,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceBlock {
    pub chain: Vec<String>,
    pub digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntervalBin {
    pub lower: f64,
    pub upper: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QubitEnvelope {
    pub mitigated: Vec<f64>,
    pub intervals: Vec<IntervalBin>,
    pub total_shots: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerFile {
    pub ingest_seq: u32,
    pub experiment_id: String,
    pub selected_matrix_id: String,
    pub normalized_probs: std::collections::HashMap<String, Vec<f64>>,
    pub drift_corrected: std::collections::HashMap<String, Vec<f64>>,
    pub envelopes: std::collections::HashMap<String, QubitEnvelope>,
    pub provenance: ProvenanceBlock,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvelopeExport {
    pub experiment_id: String,
    pub selected_matrix_id: String,
    pub envelopes: std::collections::HashMap<String, QubitEnvelope>,
    pub provenance: ProvenanceBlock,
}
