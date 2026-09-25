use ed25519_dalek::{Signature, Verifier, VerifyingKey};

use crate::canonical;
use crate::types::{KeyEntry, WitnessRow};

pub fn verify_witness_signature(witness: &WitnessRow, key: &KeyEntry) -> bool {
    let Ok(pub_bytes) = hex::decode(&key.public) else {
        return false;
    };
    let Ok(vk) = VerifyingKey::try_from(pub_bytes.as_slice()) else {
        return false;
    };
    let Ok(sig_bytes) = hex::decode(&witness.signature) else {
        return false;
    };
    let Ok(sig) = Signature::try_from(sig_bytes.as_slice()) else {
        return false;
    };
    let msg = canonical::canonical_message(
        &witness.release_id,
        &witness.artifact_digest,
        witness.epoch,
        witness.prior_witness_id.as_deref(),
    );
    vk.verify(&msg, &sig).is_ok()
}
