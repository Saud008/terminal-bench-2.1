use crate::model::{Actor, CombatEvent};

pub fn turn_order(actors: &[Actor]) -> Vec<usize> {
    let mut idxs: Vec<usize> = actors
        .iter()
        .enumerate()
        .filter(|(_, a)| a.alive)
        .map(|(i, _)| i)
        .collect();
    idxs.sort_by(|&a, &b| {
        let aa = &actors[a];
        let bb = &actors[b];
        bb.initiative
            .cmp(&aa.initiative)
            .then_with(|| aa.name.cmp(&bb.name))
    });
    let pinned: Vec<usize> = idxs.iter().copied().filter(|&i| actors[i].pinned).collect();
    let rest: Vec<usize> = idxs.into_iter().filter(|&i| !actors[i].pinned).collect();
    pinned.into_iter().chain(rest).collect()
}

pub fn mark_death(actor: &mut Actor) -> CombatEvent {
    actor.alive = false;
    actor.hp = 0;
    actor.pinned = false;
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
    actor.action_points -= 1;
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
