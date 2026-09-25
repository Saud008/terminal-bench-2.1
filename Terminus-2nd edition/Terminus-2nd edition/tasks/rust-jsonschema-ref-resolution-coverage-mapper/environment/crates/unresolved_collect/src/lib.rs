use ref_resolver::RefEdge;

pub fn unresolved_refs(edges: &[RefEdge]) -> Vec<String> {
    edges
        .iter()
        .filter(|e| e.status == "unresolved")
        .map(|e| format!("{}:{}", e.schema_id, e.ref_pointer))
        .collect()
}
