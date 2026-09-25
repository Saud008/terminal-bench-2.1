use sha2::{Digest, Sha256};

use crate::model::{CombatState, TranscriptExport};

pub fn transcript_hash(state: &CombatState) -> String {
    let payload = serde_json::to_string(&state.rounds).expect("json");
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
    format!("{:x}", hasher.finalize())
}

pub fn export_transcript(state: &CombatState) -> TranscriptExport {
    TranscriptExport {
        export_version: 1,
        seed: state.seed.clone(),
        transcript_hash: transcript_hash(state),
        rounds: state.rounds.clone(),
        actors_final: state.actors.clone(),
    }
}
