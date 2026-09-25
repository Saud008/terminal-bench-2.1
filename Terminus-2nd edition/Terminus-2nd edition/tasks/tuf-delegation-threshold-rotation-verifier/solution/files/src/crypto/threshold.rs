use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::Sha256;
use std::collections::HashSet;

use crate::canonical;
use crate::crypto::expiry;
use crate::delegation::reuse as key_reuse;
use crate::types::{KeyEntry, RoleSpec, SignatureRow};

type HmacSha256 = Hmac<Sha256>;

pub fn verify_doc(
    signed: &Value,
    signatures: &[SignatureRow],
    role: &RoleSpec,
    keys: &std::collections::BTreeMap<String, KeyEntry>,
    epoch: u64,
    root_role_keyids: &[String],
) -> (bool, u32, Vec<String>, Vec<String>) {
    let payload = canonical::canonical_bytes(signed).unwrap_or_default();
    let mut valid = 0u32;
    let mut expired = Vec::new();
    let mut reuse = Vec::new();
    let mut seen = HashSet::new();

    for sig in signatures {
        if key_reuse::is_root_role_reuse(&sig.keyid, root_role_keyids) {
            reuse.push(sig.keyid.clone());
            continue;
        }
        if !role.keyids.contains(&sig.keyid) {
            continue;
        }
        if !seen.insert(sig.keyid.clone()) {
            continue;
        }
        if let Some(key) = keys.get(&sig.keyid) {
            if !expiry::key_valid_at_epoch(key, epoch) {
                expired.push(sig.keyid.clone());
                continue;
            }
            if verify_hmac(&payload, key, &sig.sig) {
                valid += 1;
            }
        }
    }

    let met = valid >= role.threshold;
    (met, valid, expired, reuse)
}

fn verify_hmac(payload: &[u8], key: &KeyEntry, sig_hex: &str) -> bool {
    let Ok(raw) = hex::decode(&key.keyval.public) else {
        return false;
    };
    let Ok(mut mac) = HmacSha256::new_from_slice(&raw) else {
        return false;
    };
    mac.update(payload);
    let expected = hex::encode(mac.finalize().into_bytes());
    expected == sig_hex
}
