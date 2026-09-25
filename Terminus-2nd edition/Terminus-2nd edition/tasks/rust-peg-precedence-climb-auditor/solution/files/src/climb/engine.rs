use crate::climb;
use crate::grammar::{self, rule_by_name};
use crate::types::{GrammarRow, GraphFile, SpanNode};

pub fn parse_expression(
    graph: &GraphFile,
    grammar: &GrammarRow,
    tokens: &[String],
    bias: i32,
) -> Result<SpanNode, String> {
    let (node, end) = parse_with_prec(graph, grammar, tokens, 0, 0, bias)?;
    if end != tokens.len() {
        return Err("trailing tokens".into());
    }
    Ok(node)
}

fn parse_with_prec(
    graph: &GraphFile,
    grammar: &GrammarRow,
    tokens: &[String],
    mut pos: usize,
    min_prec: i32,
    bias: i32,
) -> Result<(SpanNode, usize), String> {
    let (mut left, mut next) = parse_primary(graph, grammar, tokens, pos, bias)?;
    pos = next;
    while pos < tokens.len() {
        let tok = &tokens[pos];
        let Some(prec) = climb::op_prec(tok, graph, grammar, bias) else {
            break;
        };
        if prec < min_prec {
            break;
        }
        let op = tok.clone();
        pos += 1;
        let (right, after) = parse_with_prec(graph, grammar, tokens, pos, prec + 1, bias)?;
        pos = after;
        let span = [left.span[0], right.span[1]];
        left = SpanNode {
            kind: "binary".into(),
            value: Some(op),
            span,
            recovered: false,
            children: vec![left, right],
        };
    }
    Ok((left, pos))
}

fn parse_primary(
    graph: &GraphFile,
    grammar: &GrammarRow,
    tokens: &[String],
    pos: usize,
    bias: i32,
) -> Result<(SpanNode, usize), String> {
    if pos >= tokens.len() {
        return Err("unexpected end".into());
    }

    if let Some(start_rule) = rule_by_name(grammar, &grammar.start) {
        if let crate::types::Pattern::Atomic { inner } = &start_rule.rhs {
            if let Ok(pair) = match_atomic(inner, tokens, pos) {
                return Ok(pair);
            }
        }
    }

    let tok = &tokens[pos];
    if tok.starts_with("NUM:") {
        let val = tok.strip_prefix("NUM:").unwrap_or(tok).to_string();
        return Ok((
            SpanNode {
                kind: "number".into(),
                value: Some(val),
                span: [pos, pos + 1],
                recovered: false,
                children: vec![],
            },
            pos + 1,
        ));
    }

    for rule in &grammar.rules {
        if rule.left_recursive {
            if let Some(node) = try_left_expand(graph, grammar, rule, tokens, pos, bias) {
                return Ok(node);
            }
        }
    }

    Err(format!("bad primary at {pos}"))
}

fn try_left_expand(
    graph: &GraphFile,
    grammar: &GrammarRow,
    rule: &crate::types::RuleInput,
    tokens: &[String],
    pos: usize,
    bias: i32,
) -> Option<(SpanNode, usize)> {
    if pos >= tokens.len() || !tokens[pos].starts_with("NUM:") {
        return None;
    }
    let (left, mut p) = parse_primary(graph, grammar, tokens, pos, bias).ok()?;
    if p < tokens.len() {
        if let Some(prec) = climb::op_prec(&tokens[p], graph, grammar, bias) {
            if prec >= rule.prec + bias {
                let op = tokens[p].clone();
                p += 1;
                let (right, end) =
                    parse_with_prec(graph, grammar, tokens, p, prec + 1, bias).ok()?;
                let node = SpanNode {
                    kind: "binary".into(),
                    value: Some(op),
                    span: [left.span[0], right.span[1]],
                    recovered: false,
                    children: vec![left, right],
                };
                return Some((node, end));
            }
        }
    }
    Some((left, p))
}

fn match_atomic(
    inner: &crate::types::Pattern,
    tokens: &[String],
    pos: usize,
) -> Result<(SpanNode, usize), String> {
    match inner {
        crate::types::Pattern::Token { lit } if lit == "NUMBER" => {
            if pos < tokens.len() && tokens[pos].starts_with("NUM:") {
                let val = tokens[pos].strip_prefix("NUM:").unwrap().to_string();
                return Ok((
                    SpanNode {
                        kind: "number".into(),
                        value: Some(val),
                        span: [pos, pos + 1],
                        recovered: false,
                        children: vec![],
                    },
                    pos + 1,
                ));
            }
            climb::push_recovered(SpanNode {
                kind: "error_recovery".into(),
                value: Some("atomic_fail".into()),
                span: [pos, pos],
                recovered: true,
                children: vec![],
            });
            Err("atomic boundary violated".into())
        }
        _ => Err("unsupported atomic".into()),
    }
}
