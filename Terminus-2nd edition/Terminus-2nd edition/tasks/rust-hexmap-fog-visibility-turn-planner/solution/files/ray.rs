use crate::tb3_mdist;
use crate::types::Cell;
use std::collections::HashMap;

const DIRS: [(i32, i32); 6] = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)];

pub fn hex_line(q0: i32, r0: i32, q1: i32, r1: i32) -> Vec<(i32, i32)> {
    let mut out = vec![(q0, r0)];
    let mut q = q0;
    let mut r = r0;
    let mut guard = 0;
    while (q, r) != (q1, r1) {
        let mut best: Option<(i32, i32)> = None;
        let mut best_d = i32::MAX;
        for (dq, dr) in DIRS {
            let nq = q + dq;
            let nr = r + dr;
            let d = tb3_mdist::cube_distance(nq, nr, q1, r1);
            let take = match best {
                None => true,
                Some((bq, br)) => d < best_d || (d == best_d && (nq, nr) < (bq, br)),
            };
            if take {
                best_d = d;
                best = Some((nq, nr));
            }
        }
        let (nq, nr) = best.expect("hex neighbor");
        q = nq;
        r = nr;
        out.push((q, r));
        guard += 1;
        if guard > 256 {
            break;
        }
    }
    out
}

pub fn clear_los(obs_q: i32, obs_r: i32, tgt_q: i32, tgt_r: i32, elev: &HashMap<(i32, i32), i32>) -> bool {
    let line = hex_line(obs_q, obs_r, tgt_q, tgt_r);
    if line.len() <= 2 {
        return true;
    }
    let obs_e = *elev.get(&(obs_q, obs_r)).unwrap_or(&0);
    let tgt_e = *elev.get(&(tgt_q, tgt_r)).unwrap_or(&0);
    let floor = obs_e.min(tgt_e);
    for &(q, r) in &line[1..line.len() - 1] {
        let e = *elev.get(&(q, r)).unwrap_or(&0);
        if e > floor {
            return false;
        }
    }
    true
}

pub fn elev_map(cells: &[Cell]) -> HashMap<(i32, i32), i32> {
    cells.iter().map(|c| ((c.q, c.r), c.elev)).collect()
}
