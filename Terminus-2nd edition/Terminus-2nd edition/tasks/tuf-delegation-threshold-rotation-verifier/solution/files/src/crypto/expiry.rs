use crate::types::KeyEntry;

pub fn key_valid_at_epoch(key: &KeyEntry, epoch: u64) -> bool {
    epoch < key.keyval.expires_epoch
}

pub fn expired_keyids(
    keyids: &[String],
    keys: &std::collections::BTreeMap<String, KeyEntry>,
    epoch: u64,
) -> Vec<String> {
    let mut out = Vec::new();
    for kid in keyids {
        if let Some(key) = keys.get(kid) {
            if !key_valid_at_epoch(key, epoch) {
                out.push(kid.clone());
            }
        }
    }
    out
}
