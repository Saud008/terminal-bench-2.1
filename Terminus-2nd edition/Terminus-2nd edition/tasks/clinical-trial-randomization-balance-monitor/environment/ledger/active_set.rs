use std::collections::{HashMap, HashSet};

pub fn apply_events(events: &[(String, String, String, String)]) -> (HashMap<String, String>, HashSet<String>) {
    let mut arms: HashMap<String, String> = HashMap::new();
    let mut withdrawn: HashSet<String> = HashSet::new();
    for (subject, event, arm, _site) in events {
        if event == "withdraw" {
            withdrawn.insert(subject.clone());
        } else if event == "assign" {
            arms.insert(subject.clone(), arm.clone());
        }
    }
    (arms, withdrawn)
}

pub fn active_arm_counts(
    arms: &HashMap<String, String>,
    withdrawn: &HashSet<String>,
    stratum_of: &HashMap<String, String>,
    stratum_id: &str,
) -> (u32, u32) {
    let mut a = 0u32;
    let mut b = 0u32;
    for (subject, arm) in arms {
        if withdrawn.contains(subject) {
            continue;
        }
        if stratum_of.get(subject).map(String::as_str) != Some(stratum_id) {
            continue;
        }
        if arm == "A" {
            a += 1;
        } else if arm == "B" {
            b += 1;
        }
    }
    (a, b)
}
