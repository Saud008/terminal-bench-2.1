use crate::model::SimState;

pub fn apply_input(state: &mut SimState, tick: u64, opcode: u8, value: i16) {
    state.inputs_applied += 1;
    state.tick = state.tick.max(tick);
    match opcode {
        0 => state.accumulator += i64::from(value),
        1 => state.mix ^= (tick as u64).wrapping_mul(value as u64),
        2 => state.accumulator = state.accumulator.wrapping_mul(i64::from(value.max(1))),
        _ => state.mix = state.mix.wrapping_add(value as u64),
    }
}

pub fn hash_state(state: &SimState, client_id: u32, seed: u64) -> String {
    use sha2::{Digest, Sha256};
    let payload = format!(
        "{}:{}:{}:{}:{}:{}",
        client_id, seed, state.tick, state.accumulator, state.mix, state.inputs_applied
    );
    let digest = Sha256::digest(payload.as_bytes());
    format!("{:x}", digest)
}
