use crate::model::{Actor, CombatEvent};

pub fn apply_start_of_turn(actor: &mut Actor) -> Option<CombatEvent> {
    if actor.bleed <= 0 {
        return None;
    }
    let damage = actor.bleed;
    actor.hp = (actor.hp - damage).max(0);
    actor.bleed = (actor.bleed - 1).max(0);
    Some(CombatEvent {
        kind: "bleed".into(),
        actor: actor.id.clone(),
        damage: Some(damage),
        hp_after: Some(actor.hp),
        bleed_after: Some(actor.bleed),
        ap_after: None,
    })
}
