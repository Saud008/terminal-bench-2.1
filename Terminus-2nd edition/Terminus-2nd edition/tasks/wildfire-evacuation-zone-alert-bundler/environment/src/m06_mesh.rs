use crate::hazard_schema::{Point, RoadsSpec};
use std::collections::{HashMap, VecDeque};

pub fn shortest_path_km(roads: &RoadsSpec, start: &Point, goal: &Point) -> Option<f64> {
    let start_id = nearest_node(roads, start)?;
    let goal_id = nearest_node(roads, goal)?;
    if start_id == goal_id {
        return Some(0.0);
    }
    let mut adj: HashMap<String, Vec<(String, f64)>> = HashMap::new();
    for e in &roads.edges {
        adj.entry(e.from.clone()).or_default().push((e.to.clone(), e.km));
        adj.entry(e.to.clone()).or_default().push((e.from.clone(), e.km));
    }
    let mut dist: HashMap<String, f64> = HashMap::new();
    dist.insert(start_id.clone(), 0.0);
    let mut q = VecDeque::new();
    q.push_back(start_id.clone());
    while let Some(cur) = q.pop_front() {
        let base = *dist.get(&cur).unwrap_or(&0.0);
        for (nxt, km) in adj.get(&cur).into_iter().flatten() {
            let nd = base + km;
            if dist.get(nxt).map(|d| nd < *d).unwrap_or(true) {
                dist.insert(nxt.clone(), nd);
                q.push_back(nxt.clone());
            }
        }
    }
    dist.get(&goal_id).copied()
}

fn nearest_node(roads: &RoadsSpec, p: &Point) -> Option<String> {
    roads
        .nodes
        .iter()
        .min_by(|a, b| {
            let da = (a.x - p.x).powi(2) + (a.y - p.y).powi(2);
            let db = (b.x - p.x).powi(2) + (b.y - p.y).powi(2);
            da.partial_cmp(&db).unwrap()
        })
        .map(|n| n.id.clone())
}
