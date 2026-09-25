use graph_export::build_graph;
use staging_write::{read_example_coverage, read_ref_edges};
use serde::Serialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct CoverageTotals {
    pub schema_count: u32,
    pub resolved_ref_count: u32,
    pub unresolved_ref_count: u32,
    pub recursive_ref_count: u32,
    pub example_count: u32,
}

#[derive(Debug, Serialize)]
pub struct ReportBody {
    pub totals: CoverageTotals,
    pub unresolved_refs: Vec<String>,
    pub example_coverage: Vec<serde_json::Value>,
}

pub fn publish_all(
    ref_edges_path: &Path,
    coverage_path: &Path,
    report_path: &Path,
    graph_path: &Path,
) -> Result<(), String> {
    let ref_edges = read_ref_edges(ref_edges_path)?;
    let example_coverage = read_example_coverage(coverage_path)?;
    let unresolved: Vec<String> = ref_edges
        .iter()
        .filter(|e| e.status == "unresolved")
        .map(|e| format!("{}:{}", e.schema_id, e.ref_pointer))
        .collect();
    let mut schema_ids = std::collections::BTreeSet::new();
    for e in &ref_edges {
        schema_ids.insert(e.schema_id.clone());
    }
    let totals = CoverageTotals {
        schema_count: schema_ids.len() as u32,
        resolved_ref_count: ref_edges.len() as u32,
        unresolved_ref_count: unresolved.len() as u32,
        recursive_ref_count: ref_edges.iter().filter(|e| e.status == "recursive").count() as u32,
        example_count: example_coverage.len() as u32,
    };
    let example_cov: Vec<serde_json::Value> = example_coverage
        .iter()
        .map(|c| serde_json::to_value(c).unwrap_or(serde_json::Value::Null))
        .collect();
    let report = ReportBody {
        totals,
        unresolved_refs: unresolved,
        example_coverage: example_cov,
    };
    let graph = build_graph(
        &ref_edges
            .iter()
            .map(|r| ref_resolver::RefEdge {
                schema_id: r.schema_id.clone(),
                ref_pointer: r.ref_pointer.clone(),
                target_id: r.target_id.clone(),
                status: r.status.clone(),
                anchor_name: r.anchor_name.clone(),
            })
            .collect::<Vec<_>>(),
    );
    if let Some(parent) = report_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    if let Some(parent) = graph_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(
        report_path,
        format!(
            "{}\n",
            serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
        ),
    )
    .map_err(|e| e.to_string())?;
    fs::write(
        graph_path,
        format!(
            "{}\n",
            serde_json::to_string_pretty(&graph).map_err(|e| e.to_string())?
        ),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
