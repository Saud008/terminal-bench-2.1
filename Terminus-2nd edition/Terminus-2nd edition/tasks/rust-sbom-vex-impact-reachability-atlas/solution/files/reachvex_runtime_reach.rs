use std::collections::{HashMap, HashSet, VecDeque};

use crate::types::{AtlasStage, EDGE_RUNTIME, StageEdge};

pub fn reachable_from(root: &str, edges: &[StageEdge]) -> HashSet<String> {
    bfs_reachable(root, edges)
}

pub fn reachable_packages(stage: &AtlasStage, root: &str) -> HashSet<String> {
    bfs_reachable(root, &stage.edges)
}

pub fn bfs_reachable(root: &str, edges: &[StageEdge]) -> HashSet<String> {
    let mut adj: HashMap<String, Vec<String>> = HashMap::new();
    for e in edges {
        if e.edge_kind == EDGE_RUNTIME {
            adj.entry(e.from.clone()).or_default().push(e.to.clone());
        }
    }
    let mut seen = HashSet::new();
    let mut q = VecDeque::new();
    q.push_back(root.to_string());
    seen.insert(root.to_string());
    while let Some(cur) = q.pop_front() {
        if let Some(nexts) = adj.get(&cur) {
            for n in nexts {
                if seen.insert(n.clone()) {
                    q.push_back(n.clone());
                }
            }
        }
    }
    seen
}
