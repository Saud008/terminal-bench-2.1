use std::fs;
use std::path::Path;

use crate::bleed;
use crate::error::Result;
use crate::model::{CombatEvent, CombatState, StagingDoc};
use crate::scheduler;

fn fnv1a64(s: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in s.as_bytes() {
        h ^= u64::from(*b);
        h = h.wrapping_mul(0x00000100000001B3);
    }
    h
}

fn apply_seed_mutation(actors: &mut [crate::model::Actor], seed: &str) {
    if seed.is_empty() {
        return;
    }
    let idx = (fnv1a64(seed) as usize) % actors.len();
    let delta = ((fnv1a64(&format!("{seed}:bleed")) % 3) + 1) as i32;
    actors[idx].bleed += delta;
}

pub fn simulate_combat(staging: &StagingDoc, seed: &str) -> CombatState {
    let mut actors = staging.actors.clone();
    apply_seed_mutation(&mut actors, seed);
    let mut state = CombatState {
        state_version: 1,
        seed: seed.to_string(),
        rounds_planned: staging.rounds,
        actors: actors.clone(),
        rounds: Vec::new(),
    };
    for rnd in 1..=staging.rounds {
        let mut events = Vec::new();
        for idx in scheduler::turn_order(&actors) {
            let actor = &mut actors[idx];
            if !actor.alive || actor.action_points <= 0 {
                continue;
            }
            if let Some(ev) = bleed::apply_start_of_turn(actor) {
                events.push(ev);
            }
            if actors[idx].hp <= 0 {
                events.push(scheduler::mark_death(&mut actors[idx]));
                continue;
            }
            if actors[idx].stunned {
                events.push(scheduler::handle_stun(&mut actors[idx]));
                continue;
            }
            actors[idx].action_points -= 1;
            events.push(CombatEvent {
                kind: "act".into(),
                actor: actors[idx].id.clone(),
                damage: None,
                hp_after: None,
                bleed_after: None,
                ap_after: Some(actors[idx].action_points),
            });
        }
        state.rounds.push(crate::model::RoundLog {
            round: rnd,
            events,
        });
    }
    state.actors = actors;
    state
}

pub fn write_state(path: &Path, state: &CombatState) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(state).map_err(crate::error::CombatError::Json)?;
    fs::write(path, format!("{json}\n"))?;
    Ok(())
}

pub fn read_state(path: &Path) -> Result<CombatState> {
    let raw = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&raw)?)
}
