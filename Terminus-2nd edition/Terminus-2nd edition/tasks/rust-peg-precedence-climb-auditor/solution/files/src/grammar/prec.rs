use crate::types::{ClimbRow, GrammarRow};

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
    rows.sort_by(|a, b| b.prec.cmp(&a.prec).then(a.rule.cmp(&b.rule)));
    for (idx, row) in rows.iter_mut().enumerate() {
        row.rank = idx as u32;
    }
    rows
}
