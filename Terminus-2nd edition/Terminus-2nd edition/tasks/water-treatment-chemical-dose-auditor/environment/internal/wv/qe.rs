pub fn override_allowed(user: &str, role: &str, authorized_roles: &[String], denylist: &[String]) -> bool {
    if denylist.iter().any(|d| d == user) {
        return false;
    }
    authorized_roles.iter().any(|r| r == role)
}
