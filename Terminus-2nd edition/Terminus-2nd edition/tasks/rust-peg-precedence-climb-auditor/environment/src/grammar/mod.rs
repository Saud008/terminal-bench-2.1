pub mod prec;

use crate::types::{GrammarRow, RuleInput};

pub fn operators_for_grammar(grammar: &GrammarRow, bias: i32) -> Vec<(String, i32)> {
    let mut ops = Vec::new();
    for rule in &grammar.rules {
        if let Some(op) = binary_op_token(&rule.rhs) {
            ops.push((op, rule.prec + bias));
        }
    }
    ops.sort_by(|a, b| b.1.cmp(&a.1));
    ops
}

pub fn binary_op_token(pattern: &crate::types::Pattern) -> Option<String> {
    match pattern {
        crate::types::Pattern::Choice { alts } => alts.iter().find_map(binary_op_token),
        crate::types::Pattern::Seq { items } if items.len() == 3 => {
            if let crate::types::PatternItem::Pattern {
                value: crate::types::Pattern::Token { lit },
            } = &items[1]
            {
                Some(lit.clone())
            } else {
                None
            }
        }
        _ => None,
    }
}

pub fn rule_by_name<'a>(grammar: &'a GrammarRow, name: &str) -> Option<&'a RuleInput> {
    grammar.rules.iter().find(|r| r.name == name)
}
