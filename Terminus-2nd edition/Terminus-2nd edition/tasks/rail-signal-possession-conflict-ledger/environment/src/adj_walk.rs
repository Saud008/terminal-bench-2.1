use crate::rail_model::ScenarioFile;
use std::collections::{BTreeMap, HashMap, HashSet};

pub fn build_zone_map(sf: &ScenarioFile) -> BTreeMap<String, Vec<String>> {
    let blocks: Vec<String> = sf.blocks.iter().map(|b| b.block_id.clone()).collect();
    let mut neighbors: HashMap<String, HashSet<String>> = HashMap::new();
    for b in &blocks {
        neighbors.entry(b.clone()).or_default();
    }
    for edge in &sf.adjacency {
        neighbors
            .entry(edge[0].clone())
            .or_default()
            .insert(edge[1].clone());
        neighbors
            .entry(edge[1].clone())
            .or_default()
            .insert(edge[0].clone());
    }
    let mut out = BTreeMap::new();
    for b in blocks {
        let mut zone: Vec<String> = vec![b.clone()];
        if let Some(nbs) = neighbors.get(&b) {
            for nb in nbs {
                if !zone.contains(nb) {
                    zone.push(nb.clone());
                }
            }
        }
        zone.sort();
        out.insert(b, zone);
    }
    out
}

pub fn protected_overlap(
    closure: &BTreeMap<String, Vec<String>>,
    blocks_a: &[String],
    blocks_b: &[String],
) -> bool {
    let mut set_a = HashSet::new();
    for b in blocks_a {
        if let Some(zone) = closure.get(b) {
            for z in zone {
                set_a.insert(z.clone());
            }
        }
    }
    for b in blocks_b {
        if set_a.contains(b) {
            return true;
        }
        if let Some(zone) = closure.get(b) {
            for z in zone {
                if set_a.contains(z) {
                    return true;
                }
            }
        }
    }
    false
}
