use std::collections::HashMap;

use crate::types::RawPackage;

pub fn normalize_purl(raw: &str, name: &str, version: &str) -> String {
    let trimmed_name = name.trim();
    let trimmed_version = version.trim();
    let base = if raw.contains('@') {
        raw.trim().to_string()
    } else {
        format!("pkg:cargo/{trimmed_name}@{trimmed_version}")
    };
    if let Some(slash) = base.find('/') {
        let prefix = &base[..slash];
        let rest = &base[slash..];
        let lowered = prefix
            .split(':')
            .map(|part| part.to_ascii_lowercase())
            .collect::<Vec<_>>()
            .join(":");
        return format!("{lowered}{rest}");
    }
    base.to_ascii_lowercase()
}

pub fn collapse_packages(raw: &[RawPackage]) -> Vec<(String, String, String, String)> {
    let mut map: HashMap<String, (String, String, String)> = HashMap::new();
    for pkg in raw {
        let norm = normalize_purl(&pkg.purl, &pkg.name, &pkg.version);
        let entry = map.entry(norm.clone()).or_insert((
            pkg.purl.clone(),
            pkg.name.trim().to_string(),
            pkg.version.trim().to_string(),
        ));
        if pkg.purl < entry.0 {
            *entry = (
                pkg.purl.clone(),
                pkg.name.trim().to_string(),
                pkg.version.trim().to_string(),
            );
        }
    }
    let mut rows: Vec<(String, String, String, String)> = map
        .into_iter()
        .map(|(norm, (raw, name, version))| (norm, raw, name, version))
        .collect();
    rows.sort_by(|a, b| a.0.cmp(&b.0));
    rows
}

pub fn normalize_edge_endpoint(purl: &str, name: &str, version: &str) -> String {
    normalize_purl(purl, name, version)
}
