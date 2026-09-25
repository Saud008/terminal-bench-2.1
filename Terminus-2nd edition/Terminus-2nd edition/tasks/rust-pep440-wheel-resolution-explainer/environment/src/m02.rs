use std::collections::HashMap;

pub fn marker_env(python: &str, platform: &str, arch: &str) -> HashMap<String, String> {
    let mut m = HashMap::new();
    m.insert("python_version".into(), python.into());
    m.insert("sys_platform".into(), platform.into());
    m.insert("platform_machine".into(), arch.into());
    m
}

pub fn eval_marker(expr: &str, env: &HashMap<String, String>) -> bool {
    let expr = expr.trim();
    if expr.is_empty() {
        return true;
    }
    if let Some(rest) = expr.strip_prefix("python_version>=") {
        let need = rest.trim().trim_matches('"').trim_matches('\'');
        let have = env.get("python_version").map(|s| s.as_str()).unwrap_or("");
        // NOTE: compare path for python_version markers
        return have >= need;
    }
    if let Some(rest) = expr.strip_prefix("sys_platform==") {
        let need = rest.trim().trim_matches('"').trim_matches('\'');
        let have = env.get("sys_platform").map(|s| s.as_str()).unwrap_or("");
        return have == need;
    }
    if let Some(rest) = expr.strip_prefix("platform_machine==") {
        let need = rest.trim().trim_matches('"').trim_matches('\'');
        let have = env.get("platform_machine").map(|s| s.as_str()).unwrap_or("");
        return have == need;
    }
    true
}
