# Oracle solve — task identity rust-hexmap-fog-visibility-turn-planner token 016c5d14
#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/tb3_mdist/dist.rs <<'EOF'
pub fn cube_distance(q0: i32, r0: i32, q1: i32, r1: i32) -> i32 {
    let dq = (q1 - q0).abs();
    let dr = (r1 - r0).abs();
    let ds = ((-q1 - r1) - (-q0 - r0)).abs();
    (dq + dr + ds) / 2
}
EOF

sed -i 's/if e >= floor/if e > floor/' /app/tb3_sray/ray.rs

cat > /app/tb3_scope/reach.rs <<'EOF'
pub fn vision_radius(class: &str) -> i32 {
    match class {
        "scout" => 4,
        "infantry" => 2,
        "tower" => 3,
        _ => 1,
    }
}
EOF

cat > /app/tb3_vlay/overlay.rs <<'EOF'
use crate::tb3_mdist;
use crate::tb3_sray;
use crate::tb3_scope;
use crate::types::{BoardRoster, CellRef, FogMask};
use std::collections::BTreeSet;

pub fn compute_visible(roster: &BoardRoster) -> Vec<CellRef> {
    let elev = tb3_sray::elev_map(&roster.cells);
    let mut visible = BTreeSet::new();
    for unit in &roster.units {
        let radius = tb3_scope::vision_radius(&unit.class);
        for cell in &roster.cells {
            let dist = tb3_mdist::cube_distance(unit.q, unit.r, cell.q, cell.r);
            if dist > radius {
                continue;
            }
            if tb3_sray::clear_los(unit.q, unit.r, cell.q, cell.r, &elev) {
                visible.insert(CellRef { q: cell.q, r: cell.r });
            }
        }
    }
    visible.into_iter().collect()
}

pub fn reveal(roster: &BoardRoster, prior: Option<&FogMask>) -> FogMask {
    let mut visible: BTreeSet<CellRef> = BTreeSet::new();
    if let Some(prev) = prior {
        for c in &prev.visible_cells {
            visible.insert(c.clone());
        }
    }
    for c in compute_visible(roster) {
        visible.insert(c);
    }
    FogMask {
        run_id: roster.run_id.clone(),
        fog_generation: roster.fog_generation,
        visible_cells: visible.into_iter().collect(),
    }
}
EOF

cat > /app/tb3_rout/seal.rs <<'EOF'
use crate::types::{BoardRoster, CellRef, FogAtlas, FogMask};

pub fn seal_atlas(roster: &BoardRoster, mask: &FogMask) -> FogAtlas {
    let mut visible_cells = mask.visible_cells.clone();
    visible_cells.sort_by(|a, b| (a.q, a.r).cmp(&(b.q, b.r)));
    let visible_count = visible_cells.len() as u32;
    FogAtlas {
        run_id: roster.run_id.clone(),
        board_id: roster.board_id.clone(),
        fog_generation: mask.fog_generation,
        target_reveal: roster.target_reveal,
        visible_count,
        visible_cells,
        win_condition_met: visible_count >= roster.target_reveal,
    }
}

pub fn empty_cell() -> CellRef {
    CellRef { q: 0, r: 0 }
}
EOF

cat > /app/tb3_pclk/clock.rs <<'EOF'
use crate::types::BoardRoster;

pub fn on_load_board(roster: &mut BoardRoster) {
    roster.fog_generation = 0;
}

pub fn on_reveal_fog(roster: &mut BoardRoster) {
    roster.fog_generation = roster.fog_generation.saturating_add(1);
}
EOF

cargo build --release --locked
install -m 0755 /app/target/release/fogpf /app/bin/fogpf
