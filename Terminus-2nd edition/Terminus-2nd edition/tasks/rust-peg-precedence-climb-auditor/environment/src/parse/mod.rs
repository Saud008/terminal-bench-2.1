pub mod predicate;
pub mod whitespace;

use crate::grammar;
use crate::types::{GrammarRow, Pattern, SpanNode};

pub fn normalize_tokens(tokens: &[String], grammar: &GrammarRow) -> Result<Vec<String>, String> {
    if grammar_has_binary_ops(grammar) {
        Ok(whitespace::strip_standalone_ws(tokens))
    } else {
        whitespace::filter_sequence_tokens(tokens, grammar)
    }
}

pub fn parse_sequence(grammar: &GrammarRow, tokens: &[String]) -> Result<SpanNode, String> {
    let start = grammar
        .rules
        .iter()
        .find(|r| r.name == grammar.start)
        .ok_or("start rule missing")?;
    match &start.rhs {
        Pattern::Seq { items } => parse_seq_items(items, tokens, 0, grammar),
        _ => Err("sequence grammar required".into()),
    }
}

pub fn grammar_has_binary_ops(grammar: &GrammarRow) -> bool {
    !grammar::operators_for_grammar(grammar, 0).is_empty()
}

fn parse_seq_items(
    items: &[crate::types::PatternItem],
    tokens: &[String],
    mut pos: usize,
    grammar: &GrammarRow,
) -> Result<SpanNode, String> {
    let mut children = Vec::new();
    let start = pos;
    for item in items {
        pos = whitespace::skip_ws_between(tokens, pos)?;
        let (child, next) = parse_item(item, tokens, pos, grammar)?;
        children.push(child);
        pos = next;
        if let crate::types::PatternItem::Terminator { lit } = item {
            if pos < tokens.len() && tokens[pos] == *lit {
                pos += 1;
                pos = whitespace::apply_after_terminator(tokens, pos)?;
            } else {
                return Err(format!("expected terminator {lit}"));
            }
        }
    }
    Ok(SpanNode {
        kind: "sequence".into(),
        value: None,
        span: [start, pos],
        recovered: false,
        children,
    })
}

fn parse_item(
    item: &crate::types::PatternItem,
    tokens: &[String],
    pos: usize,
    grammar: &GrammarRow,
) -> Result<(SpanNode, usize), String> {
    match item {
        crate::types::PatternItem::Pattern { value } => parse_pattern(value, tokens, pos, grammar),
        crate::types::PatternItem::Terminator { .. } => Ok((
            SpanNode {
                kind: "terminator".into(),
                value: None,
                span: [pos, pos],
                recovered: false,
                children: vec![],
            },
            pos,
        )),
    }
}

fn parse_pattern(
    pat: &Pattern,
    tokens: &[String],
    pos: usize,
    grammar: &GrammarRow,
) -> Result<(SpanNode, usize), String> {
    match pat {
        Pattern::Token { lit } if lit == "NUMBER" => {
            if pos < tokens.len() && tokens[pos].starts_with("NUM:") {
                let val = tokens[pos].strip_prefix("NUM:").unwrap().to_string();
                Ok((
                    SpanNode {
                        kind: "number".into(),
                        value: Some(val),
                        span: [pos, pos + 1],
                        recovered: false,
                        children: vec![],
                    },
                    pos + 1,
                ))
            } else {
                Err("expected number".into())
            }
        }
        Pattern::Token { lit } => {
            if pos < tokens.len() && tokens[pos] == *lit {
                Ok((
                    SpanNode {
                        kind: "token".into(),
                        value: Some(lit.clone()),
                        span: [pos, pos + 1],
                        recovered: false,
                        children: vec![],
                    },
                    pos + 1,
                ))
            } else {
                Err(format!("expected token {lit}"))
            }
        }
        Pattern::NegPred { inner } => {
            if predicate::neg_pred_matches(inner, tokens, pos) {
                return Err("neg pred succeeded".into());
            }
            let mut next = pos;
            if next < tokens.len() && !tokens[next].starts_with("NUM:") {
                next += 1;
            }
            Ok((
                SpanNode {
                    kind: "neg_pred".into(),
                    value: None,
                    span: [pos, pos],
                    recovered: false,
                    children: vec![],
                },
                next,
            ))
        }
        Pattern::Atomic { inner } => {
            match parse_pattern(inner, tokens, pos, grammar) {
                Ok(pair) => Ok(pair),
                Err(e) => {
                    crate::climb::push_recovered(SpanNode {
                        kind: "error_recovery".into(),
                        value: Some("atomic_fail".into()),
                        span: [pos, pos],
                        recovered: true,
                        children: vec![],
                    });
                    Err(e)
                }
            }
        }
        _ => Err("unsupported pattern".into()),
    }
}
