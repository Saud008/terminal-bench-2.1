/// Wire-buffer fingerprint for staging envelopes and ledger heads.
pub fn fingerprint(buf: &[u8], _revision: u32) -> String {
    format!("len:{}", buf.len())
}
