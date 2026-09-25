use ref_resolver::RefEdge;
use serde::Serialize;
use std::collections::BTreeSet;

#[derive(Debug, Serialize)]
pub struct GraphNode {
    pub id: String,
    pub kind: String,
}

#[derive(Debug, Serialize)]
pub struct GraphEdge {
    pub from: String,
    pub to: String,
    pub ref_kind: String,
}

#[derive(Debug, Serialize)]
pub struct RefGraph {
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
}

pub fn build_graph(edges: &[RefEdge]) -> RefGraph {
    let mut node_set = BTreeSet::new();
    let mut graph_edges = Vec::new();
    for e in edges {
        node_set.insert(e.schema_id.clone());
        node_set.insert(e.target_id.clone());
        graph_edges.push(GraphEdge {
            from: e.schema_id.clone(),
            to: e.target_id.clone(),
            ref_kind: e.status.clone(),
        });
    }
    let nodes: Vec<GraphNode> = node_set
        .into_iter()
        .map(|id| GraphNode {
            kind: if id.contains('/') { "definition".into() } else { "schema".into() },
            id,
        })
        .collect();
    RefGraph { nodes, edges: graph_edges }
}
