use crate::crypto::sha256::sha256_hex;

pub fn stanza_fingerprint(type_name: &str, args: &[String]) -> String {
    let mut pre = Vec::new();
    pre.extend_from_slice(type_name.to_ascii_uppercase().as_bytes());
    pre.push(b'\n');
    for a in args {
        pre.extend_from_slice(a.as_bytes());
        pre.push(b'\n');
    }
    sha256_hex(&pre)
}
