//! Legacy wrap helper — not used by ecs-migrate apply hot path.

pub fn wrap_chunk_payload(payload: &[u8]) -> Vec<u8> {
    payload.to_vec()
}
