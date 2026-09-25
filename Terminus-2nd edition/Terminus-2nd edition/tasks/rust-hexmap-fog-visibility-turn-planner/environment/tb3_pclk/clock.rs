use crate::types::BoardRoster;

pub fn on_load_board(roster: &mut BoardRoster) {
    roster.fog_generation = 0;
}

pub fn on_reveal_fog(roster: &mut BoardRoster) {
    let _ = roster;
}
