use crate::custody_types::{IntegrityFinding, ExhibitAlias};
use std::collections::HashMap;

pub fn alias_findings(aliases: &[ExhibitAlias]) -> Vec<IntegrityFinding> {
    let mut last: HashMap<String, String> = HashMap::new();
    for a in aliases {
        last.insert(a.court_alias.clone(), a.evidence_id.clone());
    }
    let mut out = Vec::new();
    for (alias, eid) in last {
        out.push(IntegrityFinding {
            evidence_id: eid,
            code: "alias_collision".into(),
            detail: alias,
        });
    }
    out
}
