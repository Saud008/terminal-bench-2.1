use crate::model::{Actor, CombatEvent};

pub fn turn_order(actors: &[Actor]) -> Vec<usize> {
    let mut idxs: Vec<usize> = actors
        .iter()
        .enumerate()
        .filter(|(_, a)| a.alive)
        .map(|(i, _)| i)
        .collect();
    idxs.sort_by(|&a, &b| actors[a].name.cmp(&actors[b].name));
    idxs
}

pub fn mark_death(actor: &mut Actor) -> CombatEvent {
    actor.alive = false;
    actor.hp = 0;
    actor.stunned = false;
    CombatEvent {
        kind: "death".into(),
        actor: actor.id.clone(),
        damage: None,
        hp_after: None,
        bleed_after: None,
        ap_after: None,
    }
}

pub fn handle_stun(actor: &mut Actor) -> CombatEvent {
    actor.action_points -= 2;
    actor.stunned = false;
    CombatEvent {
        kind: "stun_skip".into(),
        actor: actor.id.clone(),
        damage: None,
        hp_after: None,
        bleed_after: None,
        ap_after: Some(actor.action_points),
    }
}
