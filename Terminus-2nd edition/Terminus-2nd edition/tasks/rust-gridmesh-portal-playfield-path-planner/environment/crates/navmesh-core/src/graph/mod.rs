pub mod link;

use crate::model::{CellNode, Graph, MeshBundle, NodeId, Q16};
use crate::seed::{perturb_cost_q16, synthetic_offmesh};
use link::add_bidir_edge;

pub fn build_graph(mesh: &MeshBundle, seed: u64) -> Result<Graph, String> {
    let mut nodes = std::collections::HashMap::new();
    for cell in &mesh.cells {
        nodes.insert(
            cell.id.clone(),
            CellNode {
                id: cell.id.clone(),
                gx: cell.gx,
                gy: cell.gy,
                walkable: cell.walkable,
                region: cell.region,
            },
        );
    }

    let mut graph = Graph {
        nodes,
        adj: std::collections::HashMap::new(),
    };

    for edge in &mesh.edges {
        let cost = perturb_cost_q16(edge.cost_q16, seed);
        add_bidir_edge(&mut graph, &edge.from, &edge.to, cost);
    }

    for portal in &mesh.portals {
        add_bidir_edge(&mut graph, &portal.from, &portal.to, portal.cost_q16);
    }

    for link in &mesh.offmesh {
        add_bidir_edge(&mut graph, &link.from, &link.to, link.cost_q16);
    }

    if let Some(seed_link) = synthetic_offmesh(seed, mesh) {
        add_bidir_edge(&mut graph, &seed_link.from, &seed_link.to, seed_link.cost_q16);
    }

    Ok(graph)
}

pub fn node_id(id: &str) -> NodeId {
    id.to_string()
}

pub fn edge_cost_raw(cost_q16: Q16) -> f64 {
    link::edge_weight_for_path(cost_q16)
}
