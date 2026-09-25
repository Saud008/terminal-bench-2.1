pub fn override_allowed(user: &str, role: &str, authorized_roles: &[String], denylist: &[String]) -> bool {
    if denylist.iter().any(|d| d == user) {
        return false;
    }
    let role_lower = role.to_ascii_lowercase();
    authorized_roles.iter().any(|r| r.to_ascii_lowercase() == role_lower)
}
