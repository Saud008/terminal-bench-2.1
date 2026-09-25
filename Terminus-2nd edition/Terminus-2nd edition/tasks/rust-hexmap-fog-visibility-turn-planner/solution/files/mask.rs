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
