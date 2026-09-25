pub fn is_root_role_reuse(keyid: &str, root_role_keyids: &[String]) -> bool {
    root_role_keyids.iter().any(|kid| kid == keyid)
}
