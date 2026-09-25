use crate::cost;
use crate::graph::build_graph;
use crate::model::{MeshBundle, PathExport};
use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap, HashSet};

fn dijkstra(
    graph: &crate::model::Graph,
    start: &str,
    goal: &str,
) -> (Vec<String>, Vec<f64>) {
    let mut dist: HashMap<String, f64> = HashMap::new();
    let mut parent: HashMap<String, Option<String>> = HashMap::new();
    let mut heap = BinaryHeap::new();
    let mut seen = HashSet::new();

    dist.insert(start.to_string(), 0.0);
    parent.insert(start.to_string(), None);
    heap.push(Reverse((0u64, start.to_string())));

    while let Some(Reverse((_, node))) = heap.pop() {
        if !seen.insert(node.clone()) {
            continue;
        }
        let cost = dist.get(&node).copied().unwrap_or(f64::INFINITY);
        if node == goal {
            break;
        }
        for (nxt, step_q16) in graph.adj.get(&node).into_iter().flatten() {
            let step = crate::graph::link::edge_weight_for_path(*step_q16);
            let nxt_cost = cost + step;
            if nxt_cost < *dist.get(nxt).unwrap_or(&f64::INFINITY) {
                dist.insert(nxt.clone(), nxt_cost);
                parent.insert(nxt.clone(), Some(node.clone()));
                let milli = (nxt_cost * 1_000_000.0).round() as u64;
                heap.push(Reverse((milli, nxt.clone())));
            }
        }
    }

    if !seen.contains(goal) {
        return (Vec::new(), Vec::new());
    }

    let mut path = Vec::new();
    let mut cur = Some(goal.to_string());
    while let Some(id) = cur {
        path.push(id.clone());
        cur = parent.get(&id).cloned().flatten();
    }
    path.reverse();

    let mut edge_costs = Vec::new();
    for w in path.windows(2) {
        let outs = graph.adj.get(&w[0]).cloned().unwrap_or_default();
        let step = outs
            .iter()
            .find(|(n, _)| n == &w[1])
            .map(|(_, c)| crate::graph::link::edge_weight_for_path(*c))
            .unwrap_or(0.0);
        edge_costs.push(step);
    }

    (path, edge_costs)
}

pub fn find_path(mesh: &MeshBundle, seed: u64, from: &str, to: &str) -> Result<PathExport, String> {
    if !mesh.cells.iter().any(|c| c.id == from) {
        return Err(format!("unknown from cell {from}"));
    }
    if !mesh.cells.iter().any(|c| c.id == to) {
        return Err(format!("unknown to cell {to}"));
    }

    let graph = build_graph(mesh, seed)?;
    let (path, edge_costs) = dijkstra(&graph, from, to);
    if path.is_empty() {
        return Ok(PathExport {
            mesh_id: mesh.mesh_id.clone(),
            seed,
            from: from.to_string(),
            to: to.to_string(),
            status: "unreachable".into(),
            cost_q16: 0,
            path,
        });
    }

    Ok(PathExport {
        mesh_id: mesh.mesh_id.clone(),
        seed,
        from: from.to_string(),
        to: to.to_string(),
        status: "ok".into(),
        cost_q16: cost::path_total_q16(&edge_costs),
        path,
    })
}
