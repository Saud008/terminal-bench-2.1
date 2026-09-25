use crate::crypto::sha256::sha256_hex;

pub fn stanza_fingerprint(type_name: &str, args: &[String]) -> String {
    let mut pre = Vec::new();
    pre.extend_from_slice(type_name.as_bytes());
    for a in args {
        pre.push(0x1f);
        pre.extend_from_slice(a.as_bytes());
    }
    sha256_hex(&pre)
}
