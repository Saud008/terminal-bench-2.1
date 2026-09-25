use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedTreeHead {
    pub tree_size: u64,
    pub timestamp: u64,
    pub sha256_root_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WitnessCheckpoint {
    pub witness_id: String,
    pub log_id: String,
    pub tree_size: u64,
    pub sha256_root_hash: String,
    pub timestamp: u64,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofStepJson {
    pub hash: String,
    pub side: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InclusionProof {
    pub leaf_index: u64,
    pub leaf_input: String,
    pub audit_path: Vec<ProofStepJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsistencyProof {
    pub from_size: u64,
    pub to_size: u64,
    pub audit_path: Vec<ProofStepJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditBundle {
    pub log_id: String,
    pub older_sth: SignedTreeHead,
    pub newer_sth: SignedTreeHead,
    pub inclusion: InclusionProof,
    pub consistency: ConsistencyProof,
}

#[derive(Debug)]
pub struct ParseError;

pub fn normalize_root(hex_str: &str) -> String {
    hex_str.to_string()
}

pub fn load_audit_bundle(path: &Path) -> Result<AuditBundle, ParseError> {
    let raw = fs::read_to_string(path).map_err(|_| ParseError)?;
    serde_json::from_str(&raw).map_err(|_| ParseError)
}

pub fn load_witness_file(path: &Path) -> Result<Vec<WitnessCheckpoint>, ParseError> {
    #[derive(Deserialize)]
    struct Wrap {
        checkpoints: Vec<WitnessCheckpoint>,
    }
    let raw = fs::read_to_string(path).map_err(|_| ParseError)?;
    let wrap: Wrap = serde_json::from_str(&raw).map_err(|_| ParseError)?;
    Ok(wrap.checkpoints)
}

pub fn load_bundles_from_index(index_path: &Path) -> Result<Vec<AuditBundle>, ParseError> {
    #[derive(Deserialize)]
    struct IndexEntry {
        log_id: String,
        bundle_file: String,
    }
    #[derive(Deserialize)]
    struct IndexFile {
        entries: Vec<IndexEntry>,
    }
    let root = index_path.parent().ok_or(ParseError)?;
    let raw = fs::read_to_string(index_path).map_err(|_| ParseError)?;
    let index: IndexFile = serde_json::from_str(&raw).map_err(|_| ParseError)?;
    let mut bundles = Vec::new();
    for entry in index.entries {
        let p = root.join(entry.bundle_file);
        bundles.push(load_audit_bundle(&p)?);
    }
    bundles.sort_by(|a, b| a.log_id.cmp(&b.log_id));
    Ok(bundles)
}



