use sha2::{Digest, Sha256};

use crate::model::{CombatEvent, CombatState, RoundLog, TranscriptExport};

pub fn transcript_hash(state: &CombatState) -> String {
    let payload = serde_json::to_string(&state.rounds).expect("json");
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn merge_round_events(events: &[CombatEvent]) -> Vec<CombatEvent> {
    let mut acts: Vec<CombatEvent> = Vec::new();
    let mut bleeds: Vec<CombatEvent> = Vec::new();
    let mut rest: Vec<CombatEvent> = Vec::new();
    for ev in events {
        match ev.kind.as_str() {
            "act" | "stun_skip" => acts.push(ev.clone()),
            "bleed" => bleeds.push(ev.clone()),
            _ => rest.push(ev.clone()),
        }
    }
    let mut out = rest;
    out.extend(acts);
    out.extend(bleeds);
    out
}

pub fn export_transcript(state: &CombatState) -> TranscriptExport {
    let rounds: Vec<RoundLog> = state
        .rounds
        .iter()
        .map(|r| RoundLog {
            round: r.round,
            events: merge_round_events(&r.events),
        })
        .collect();
    let mut merged_state = state.clone();
    merged_state.rounds = rounds.clone();
    TranscriptExport {
        export_version: 1,
        seed: state.seed.clone(),
        transcript_hash: transcript_hash(&merged_state),
        rounds,
        actors_final: state.actors.clone(),
    }
}
