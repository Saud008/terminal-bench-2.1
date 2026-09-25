use crate::types::RevocationRow;

pub fn is_revoked(keyid: &str, revocations: &[RevocationRow], epoch: u64) -> bool {
    for row in revocations {
        if row.keyid == keyid && epoch >= row.revoked_epoch {
            return true;
        }
    }
    false
}
