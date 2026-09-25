pub mod span;

use std::fs;

use sha2::{Digest, Sha256};

use crate::staging;
use crate::types::{AuditFile, ParseTreeFile, SpanLedgerRow, SpanNode};

pub fn audit_export(
    graph_path: &str,
    parse_path: &str,
    audit_path: &str,
    checksum_path: &str,
) -> Result<(), String> {
    let graph = staging::load_graph(graph_path)?;
    let raw = fs::read_to_string(parse_path).map_err(|e| e.to_string())?;
    let tree: ParseTreeFile = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

    let spans = span::collect_spans(&tree.root, false);
    let audit = AuditFile {
        grammar_id: tree.grammar_id.clone(),
        ingest_seq: graph.ingest_seq,
        spans,
    };

    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&audit).map_err(|e| e.to_string())?;
    fs::write(audit_path, format!("{pretty}\n")).map_err(|e| e.to_string())?;

    let digest = checksum_from_audit(&audit)?;
    fs::write(checksum_path, format!("{digest}\n")).map_err(|e| e.to_string())
}

pub fn checksum_from_audit(audit: &AuditFile) -> Result<String, String> {
    let bytes = serde_json::to_vec(audit).map_err(|e| e.to_string())?;
    let hash = Sha256::digest(bytes);
    Ok(hex::encode(hash))
}

pub fn flatten_node(node: &SpanNode, out: &mut Vec<SpanLedgerRow>, include_recovered: bool) {
    if include_recovered || !node.recovered {
        out.push(SpanLedgerRow {
            kind: node.kind.clone(),
            span: node.span,
            recovered: node.recovered,
        });
    }
    for child in &node.children {
        flatten_node(child, out, include_recovered);
    }
}
