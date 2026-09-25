use crate::types::{BoardDoc, BoardRoster, Unit};

pub fn roster_from_board(run_id: &str, board: BoardDoc) -> BoardRoster {
    BoardRoster {
        run_id: run_id.to_string(),
        board_id: board.board_id,
        target_reveal: board.target_reveal,
        fog_generation: 0,
        cells: board.cells,
        units: board.units,
    }
}

pub fn refresh_units(roster: &mut BoardRoster) {
    let mut units: Vec<Unit> = roster.units.clone();
    units.sort_by(|a, b| a.unit_id.cmp(&b.unit_id));
    roster.units = units;
}
