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
