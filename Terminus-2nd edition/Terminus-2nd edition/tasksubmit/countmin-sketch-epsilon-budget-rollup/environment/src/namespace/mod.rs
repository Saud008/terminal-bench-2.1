pub fn namespaced_bytes(namespace_salt: &str, key: &str) -> Vec<u8> {
    let mut out = key.as_bytes().to_vec();
    out.extend_from_slice(namespace_salt.as_bytes());
    out
}
