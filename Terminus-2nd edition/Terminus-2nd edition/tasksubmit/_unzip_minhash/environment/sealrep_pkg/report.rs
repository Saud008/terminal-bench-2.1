use crate::types::{ClusterGraph, ProvenanceCluster, ProvenanceReport, SketchIndex};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

pub fn audit_digest(report: &ProvenanceReport) -> String {
    let body = serde_json::json!({
        "cluster_count": report.cluster_count,
        "jaccard_floor": report.jaccard_floor,
        "run_id": report.run_id,
        "singleton_count": report.singleton_count,
        "total_documents": report.total_documents,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_report(cfg: &crate::types::Config, run_id: &str) -> Result<ProvenanceReport, String> {
    let sketch: SketchIndex = serde_json::from_str(
        &fs::read_to_string(PathBuf::from(&cfg.sketch_index_dir).join(format!("{run_id}.json")))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let graph: ClusterGraph = serde_json::from_str(
        &fs::read_to_string(PathBuf::from(&cfg.cluster_graph_dir).join(format!("{run_id}.json")))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    let path_by_id: BTreeMap<String, String> = sketch
        .documents
        .iter()
        .map(|d| (d.doc_id.clone(), d.source_path.clone()))
        .collect();

    let mut clusters = Vec::new();
    for c in &graph.clusters {
        let source_paths: Vec<String> = c
            .member_doc_ids
            .iter()
            .filter_map(|id| path_by_id.get(id).cloned())
            .collect();
        clusters.push(ProvenanceCluster {
            cluster_id: c.cluster_id.clone(),
            representative_doc_id: c.representative_doc_id.clone(),
            member_doc_ids: c.member_doc_ids.clone(),
            source_paths,
            min_pairwise_estimate: c.min_pairwise_estimate,
        });
    }

    let singleton_count = clusters.iter().filter(|c| c.member_doc_ids.len() == 1).count() as u32;
    let report = ProvenanceReport {
        run_id: run_id.to_string(),
        cluster_run_id: graph.cluster_run_id.clone(),
        jaccard_floor: graph.jaccard_floor,
        total_documents: sketch.documents.len() as u32,
        cluster_count: clusters.len() as u32,
        singleton_count,
        clusters,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&report);
    Ok(ProvenanceReport {
        audit_digest: digest,
        ..report
    })
}

pub fn write_report(cfg: &crate::types::Config, run_id: &str, output: &Path) -> Result<(), String> {
    let report = build_report(cfg, run_id)?;
    fs::write(
        output,
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
