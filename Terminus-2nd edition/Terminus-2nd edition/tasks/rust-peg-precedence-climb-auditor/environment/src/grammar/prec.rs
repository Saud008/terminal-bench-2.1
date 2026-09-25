use crate::types::{ClimbRow, GrammarRow};

/// Build climb table for all grammars in staging.
pub fn build_climb_table(grammars: &[GrammarRow]) -> Vec<ClimbRow> {
    let mut rows: Vec<ClimbRow> = Vec::new();
    for grammar in grammars {
        for rule in &grammar.rules {
            rows.push(ClimbRow {
                rule: format!("{}::{}", grammar.grammar_id, rule.name),
                prec: rule.prec,
                rank: rule.decl_order,
                left_recursive: rule.left_recursive,
            });
        }
    }
    rows.sort_by_key(|r| r.rank);
    for (idx, row) in rows.iter_mut().enumerate() {
        row.rank = idx as u32;
    }
    rows
}
