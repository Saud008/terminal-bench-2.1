use crate::cost;
use crate::model::{Graph, NodeId, Q16};

pub fn add_bidir_edge(graph: &mut Graph, from: &str, to: &str, cost_q16: Q16) {
    let weight = cost::edge_weight(cost_q16);
    graph
        .adj
        .entry(from.to_string())
        .or_default()
        .push((to.to_string(), weight as Q16));
}

pub fn edge_weight_for_path(cost_q16: Q16) -> f64 {
    cost::edge_weight(cost_q16)
}

pub fn has_reverse(graph: &Graph, from: &NodeId, to: &NodeId) -> bool {
    graph
        .adj
        .get(to)
        .map(|outs| outs.iter().any(|(n, _)| n == from))
        .unwrap_or(false)
}
