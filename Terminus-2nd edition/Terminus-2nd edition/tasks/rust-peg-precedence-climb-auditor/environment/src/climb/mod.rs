pub mod engine;

use std::cell::RefCell;
use std::fs;

use crate::grammar;
use crate::staging;
use crate::types::{GrammarRow, GraphFile, ParseTreeFile, SpanNode, TokenInput};

thread_local! {
    static RECOVERED: RefCell<Vec<SpanNode>> = RefCell::new(Vec::new());
}

pub fn run_parse(graph_path: &str, input_path: &str, out_path: &str) -> Result<(), String> {
    RECOVERED.with(|r| r.borrow_mut().clear());
    let graph = staging::load_graph(graph_path)?;
    let raw = fs::read_to_string(input_path).map_err(|e| e.to_string())?;
    let input: TokenInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let grammar = staging::grammar_by_id(&graph, &input.grammar_id)
        .ok_or_else(|| format!("grammar {} not found", input.grammar_id))?;

    let bias: i32 = std::env::var("TB3_PREC_BIAS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);

    let tokens = crate::parse::normalize_tokens(&input.tokens, grammar)?;
    let root = if crate::parse::grammar_has_binary_ops(grammar) {
        engine::parse_expression(&graph, grammar, &tokens, bias)?
    } else {
        crate::parse::parse_sequence(grammar, &tokens)?
    };
    let recovered = RECOVERED.with(|r| r.borrow().clone());

    let tree = ParseTreeFile {
        grammar_id: input.grammar_id.clone(),
        root,
        recovered_nodes: recovered,
    };
    let parent = std::path::Path::new(out_path)
        .parent()
        .unwrap_or(std::path::Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(&tree).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn push_recovered(node: SpanNode) {
    RECOVERED.with(|r| r.borrow_mut().push(node));
}

pub fn op_prec(token: &str, graph: &GraphFile, grammar: &GrammarRow, bias: i32) -> Option<i32> {
    for rule in &grammar.rules {
        if let Some(op) = grammar::binary_op_token(&rule.rhs) {
            if op == token {
                let key = format!("{}::{}", grammar.grammar_id, rule.name);
                if let Some(row) = graph.climb_table.iter().find(|r| r.rule == key) {
                    return Some(row.rank as i32 + bias);
                }
                return Some(rule.prec + bias);
            }
        }
    }
    None
}
