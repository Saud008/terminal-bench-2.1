pub fn namespaced_bytes(namespace_salt: &str, key: &str) -> Vec<u8> {
    let mut out = namespace_salt.as_bytes().to_vec();
    out.push(0x1f);
    out.extend_from_slice(key.as_bytes());
    out
}
