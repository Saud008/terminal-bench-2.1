use graph_ir::{read_graph_dir, GraphDoc};
use propagate::propagate_graph;
use serde::Serialize;
use staging_store::{read_staging, StagedRow};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

// Export path: emit constraint diagnostics from staged ledger rows.

#[derive(Debug, Serialize, Clone)]
pub struct Violation {
    pub node_id: String,
    pub op: String,
    pub tensor: String,
    pub code: String,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct AuditReport {
    pub graph_id: String,
    pub violations: Vec<Violation>,
    pub totals: Totals,
}

#[derive(Debug, Serialize)]
pub struct Totals {
    pub violation_count: u32,
    pub tensor_count: u32,
}

pub fn stage_audit_out(staging_path: &Path, graph_dir: &Path, out_path: &Path) -> Result<(), String> {
    let staged = read_staging(staging_path)?;
    let docs = read_graph_dir(graph_dir)?;
    let mut by_graph: BTreeMap<String, Vec<StagedRow>> = BTreeMap::new();
    for row in staged {
        by_graph.entry(row.graph_id.clone()).or_default().push(row);
    }
    let mut reports = Vec::new();
    for doc in docs {
        let rows = by_graph.get(&doc.graph_id).cloned().unwrap_or_default();
        let violations = delta_violation_rows(&doc, &rows);
        let tensor_count = rows.len() as u32;
        let unique_nodes: std::collections::BTreeSet<_> = violations.iter().map(|v| v.node_id.clone()).collect();
        reports.push(AuditReport {
            graph_id: doc.graph_id.clone(),
            violations: violations.clone(),
            totals: Totals {
                violation_count: unique_nodes.len() as u32,
                tensor_count,
            },
        });
    }
    let json = serde_json::to_string_pretty(&reports).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}

fn delta_violation_rows(doc: &GraphDoc, staged: &[StagedRow]) -> Vec<Violation> {
    let expected = propagate_graph(doc).unwrap_or_default();
    let mut exp_map: BTreeMap<String, _> = BTreeMap::new();
    for row in expected {
        exp_map.insert(row.tensor.clone(), row);
    }
    let mut violations = Vec::new();
    for row in staged {
        let Some(exp) = exp_map.get(&row.tensor) else {
            violations.push(Violation {
                node_id: row.node_id.clone(),
                op: "Missing".into(),
                tensor: row.tensor.clone(),
                code: "UNKNOWN_TENSOR".into(),
                message: "tensor not in reference propagation".into(),
            });
            continue;
        };
        let exp_json = propagate::shape_vec_to_json(&exp.shape);
        if exp_json != row.shape {
            let op = doc
                .nodes
                .iter()
                .find(|n| n.id == row.node_id)
                .map(|n| n.op.clone())
                .unwrap_or_else(|| "Input".into());
            violations.push(Violation {
                node_id: row.node_id.clone(),
                op,
                tensor: row.tensor.clone(),
                code: "SHAPE_MISMATCH".into(),
                message: "propagated shape differs from contract".into(),
            });
        }
    }
    violations
}
