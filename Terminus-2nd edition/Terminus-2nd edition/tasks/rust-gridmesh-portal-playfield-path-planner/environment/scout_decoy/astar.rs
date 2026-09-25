//! Scout decoy A* sandbox — float-cost pathfinding toy.
//! Not imported by the validate / path playtest hot path.

#![allow(dead_code)]

/// Float-cost heuristic used only by this decoy sandbox.
pub fn float_edge_weight(cost_q16: i32) -> f64 {
    (cost_q16 as f64) / 65536.0
}

/// Toy A* step that truncates float costs — must stay off the hot path.
pub fn decoy_step_cost(accum: f64, edge_q16: i32) -> f64 {
    accum + float_edge_weight(edge_q16)
}
