use doc_loader::{load_directory, SchemaDoc};
use example_runner::{evaluate_examples, ExampleCoverage, ExampleRow};
use ref_resolver::{resolve_all, RefEdge};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
pub struct StagingRow {
    pub schema_id: String,
    pub ref_pointer: String,
    pub target_id: String,
    pub status: String,
    pub anchor_name: Option<String>,
}

pub fn trace(
    schema_dir: &Path,
    examples_path: &Path,
    ref_edges_path: &Path,
    coverage_path: &Path,
) -> Result<(), String> {
    let docs = load_directory(schema_dir)?;
    let edges = resolve_all(&docs, schema_dir);
    let examples = load_examples(examples_path)?;
    let coverage = evaluate_examples(&docs, &examples);

    let mut edge_lines: Vec<String> = edges
        .into_iter()
        .map(|e| {
            let row = StagingRow {
                schema_id: e.schema_id,
                ref_pointer: e.ref_pointer,
                target_id: e.target_id,
                status: e.status,
                anchor_name: e.anchor_name,
            };
            serde_json::to_string(&row).map_err(|err| err.to_string())
        })
        .collect::<Result<_, _>>()?;
    edge_lines.sort();
    if let Some(parent) = ref_edges_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(ref_edges_path, format!("{}\n", edge_lines.join("\n"))).map_err(|e| e.to_string())?;

    let mut cov_lines: Vec<String> = coverage
        .into_iter()
        .map(|c| serde_json::to_string(&c).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    cov_lines.sort();
    if let Some(parent) = coverage_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(coverage_path, format!("{}\n", cov_lines.join("\n"))).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn read_ref_edges(path: &Path) -> Result<Vec<StagingRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}

pub fn read_example_coverage(path: &Path) -> Result<Vec<ExampleCoverage>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}

fn load_examples(path: &Path) -> Result<Vec<ExampleRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn docs_for_tests(dir: &Path) -> Result<Vec<SchemaDoc>, String> {
    load_directory(dir)
}

pub fn edges_for_tests(docs: &[SchemaDoc], dir: &Path) -> Vec<RefEdge> {
    resolve_all(docs, dir)
}
