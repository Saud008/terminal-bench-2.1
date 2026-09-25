use crate::types::DelegationRow;

pub fn pick_delegation<'a>(path: &str, delegations: &'a [DelegationRow]) -> Option<&'a DelegationRow> {
    let mut best: Option<(&DelegationRow, usize)> = None;
    for deleg in delegations {
        for pattern in &deleg.paths {
            if pattern_matches(path, pattern) {
                let score = pattern.len();
                match best {
                    None => best = Some((deleg, score)),
                    Some((_, prev)) if score > prev => best = Some((deleg, score)),
                    _ => {}
                }
            }
        }
    }
    best.map(|(d, _)| d)
}

pub fn target_allowed(path: &str, delegations: &[DelegationRow]) -> (bool, Option<String>, String) {
    if let Some(deleg) = pick_delegation(path, delegations) {
        for pattern in &deleg.paths {
            if pattern_matches(path, pattern) {
                return (true, Some(deleg.name.clone()), "ok".into());
            }
        }
        return (false, Some(deleg.name.clone()), "pattern_mismatch".into());
    }
    (false, None, "no_delegation".into())
}

fn pattern_matches(path: &str, pattern: &str) -> bool {
    if pattern.contains("**") {
        let prefix = pattern.trim_end_matches("/**");
        return path.starts_with(prefix);
    }
    if pattern.contains('*') {
        let parts: Vec<&str> = pattern.split('/').collect();
        let path_parts: Vec<&str> = path.split('/').collect();
        if parts.len() != path_parts.len() {
            return false;
        }
        for (p, t) in parts.iter().zip(path_parts.iter()) {
            if *p != "*" && p != t {
                return false;
            }
        }
        return true;
    }
    path == pattern
}

pub fn literal_score(pattern: &str) -> usize {
    pattern.chars().filter(|c| *c != '*' && *c != '/').count()
}
