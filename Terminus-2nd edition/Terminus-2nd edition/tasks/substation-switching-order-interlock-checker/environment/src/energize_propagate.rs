use crate::yard_model::BreakerStates;
use std::collections::{BTreeSet, HashMap, HashSet};

pub fn compute_energized(
    sources: &[String],
    breakers: &[(String, String, String)],
    states: &BreakerStates,
) -> Vec<String> {
    let mut energized: HashSet<String> = sources.iter().cloned().collect();
    let mut closed: HashMap<String, Vec<String>> = HashMap::new();
    for (id, from, to) in breakers {
        if states.get(id).map(|s| s.as_str()) != Some("closed") {
            continue;
        }
        closed.entry(from.clone()).or_default().push(to.clone());
        closed.entry(to.clone()).or_default().push(from.clone());
    }
    let mut changed = true;
    while changed {
        changed = false;
        let snapshot: Vec<String> = energized.iter().cloned().collect();
        for bus in snapshot {
            if let Some(nbs) = closed.get(&bus) {
                for nb in nbs {
                    if energized.insert(nb.clone()) {
                        changed = true;
                    }
                }
            }
        }
    }
    let mut out: BTreeSet<String> = energized.into_iter().collect();
    out.into_iter().collect()
}
