//! Pathfinding sandbox for scout path previews. Not invoked by fogpf CLI subcommands.

use std::collections::{HashMap, HashSet};

pub fn shortest_steps(
    start: (i32, i32),
    goal: (i32, i32),
    walkable: &HashSet<(i32, i32)>,
) -> Option<i32> {
    if !walkable.contains(&start) || !walkable.contains(&goal) {
        return None;
    }
    let mut open: Vec<(i32, i32, i32)> = vec![(0, start.0, start.1)];
    let mut gscore = HashMap::new();
    gscore.insert(start, 0);
    let dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)];
    while !open.is_empty() {
        open.sort_by_key(|n| n.0);
        let (_, q, r) = open.remove(0);
        if (q, r) == goal {
            return gscore.get(&(q, r)).copied();
        }
        let base = *gscore.get(&(q, r)).unwrap_or(&i32::MAX);
        for (dq, dr) in dirs {
            let nq = q + dq;
            let nr = r + dr;
            if !walkable.contains(&(nq, nr)) {
                continue;
            }
            let tentative = base + 1;
            let prev = gscore.get(&(nq, nr)).copied().unwrap_or(i32::MAX);
            if tentative < prev {
                gscore.insert((nq, nr), tentative);
                let h = (nq - goal.0).abs() + (nr - goal.1).abs();
                open.push((tentative + h, nq, nr));
            }
        }
    }
    None
}
