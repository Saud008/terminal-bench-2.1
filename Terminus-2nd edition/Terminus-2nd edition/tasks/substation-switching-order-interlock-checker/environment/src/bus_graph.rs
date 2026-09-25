use crate::yard_model::{BreakerRow, ScenarioFile};
use std::collections::BTreeSet;

pub fn build_adjacency(sf: &ScenarioFile) -> Vec<[String; 2]> {
    let mut edges: BTreeSet<(String, String)> = BTreeSet::new();
    for br in &sf.breakers {
        let a = br.from_bus.clone();
        let b = br.to_bus.clone();
        if a <= b {
            edges.insert((a, b));
        } else {
            edges.insert((b, a));
        }
    }
    edges
        .into_iter()
        .map(|(a, b)| [a, b])
        .collect()
}
