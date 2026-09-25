use crate::yard_model::{BreakerRow, BreakerStates};

pub fn initial_states(rows: &[BreakerRow]) -> BreakerStates {
    let mut m = BreakerStates::new();
    for r in rows {
        m.insert(r.breaker_id.clone(), r.initial_state.clone());
    }
    m
}

pub fn apply_action(states: &mut BreakerStates, breaker_id: &str, action: &str) -> bool {
    let Some(cur) = states.get_mut(breaker_id) else {
        return false;
    };
    *cur = if action == "open" {
        "open".into()
    } else {
        "closed".into()
    };
    true
}
