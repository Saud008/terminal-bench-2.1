use crate::types::DelegationRow;

pub fn pick_delegation<'a>(path: &str, delegations: &'a [DelegationRow]) -> Option<&'a DelegationRow> {
    let mut best: Option<(&DelegationRow, usize, &str)> = None;
    for deleg in delegations {
        for pattern in &deleg.paths {
            if pattern_matches(path, pattern) {
                let score = literal_score(pattern);
                match best {
                    None => best = Some((deleg, score, &deleg.name)),
                    Some((_, prev_score, prev_name)) => {
                        if score > prev_score || (score == prev_score && deleg.name.as_str() < prev_name) {
                            best = Some((deleg, score, &deleg.name));
                        }
                    }
                }
            }
        }
    }
    best.map(|(d, _, _)| d)
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
        return path.starts_with(prefix) && (path.len() == prefix.len() || path[prefix.len()..].starts_with('/'));
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
