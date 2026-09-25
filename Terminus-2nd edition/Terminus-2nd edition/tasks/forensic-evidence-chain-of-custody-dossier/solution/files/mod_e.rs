use crate::custody_types::{IntegrityFinding, ExhibitAlias};
use std::collections::HashMap;

pub fn alias_findings(aliases: &[ExhibitAlias]) -> Vec<IntegrityFinding> {
    let mut seen: HashMap<String, String> = HashMap::new();
    let mut out = Vec::new();
    for a in aliases {
        if let Some(prior) = seen.get(&a.court_alias) {
            if prior != &a.evidence_id {
                out.push(IntegrityFinding {
                    evidence_id: a.evidence_id.clone(),
                    code: "alias_collision".into(),
                    detail: a.court_alias.clone(),
                });
            }
        } else {
            seen.insert(a.court_alias.clone(), a.evidence_id.clone());
        }
    }
    out
}
