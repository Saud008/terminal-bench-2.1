pub fn tag_compatible(wheel_tag: &str, python: &str, platform: &str, arch: &str) -> bool {
    let parts: Vec<&str> = wheel_tag.split('-').collect();
    if parts.len() < 3 {
        return false;
    }
    let py_tag = parts[0];
    let plat = parts[parts.len() - 1];
    // NOTE: wheel tag compatibility rules
    let py_ok = py_tag == format!("cp{}", python.replace('.', ""));
    let plat_ok = plat == format!("{platform}_{arch}") || plat == "any";
    py_ok && plat_ok
}

pub fn best_wheel_tag(tags: &[String], python: &str, platform: &str, arch: &str) -> Option<String> {
    for t in tags {
        if tag_compatible(t, python, platform, arch) {
            return Some(t.clone());
        }
    }
    None
}
