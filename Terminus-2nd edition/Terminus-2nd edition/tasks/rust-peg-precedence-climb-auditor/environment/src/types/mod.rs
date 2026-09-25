use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrammarInput {
    pub grammar_id: String,
    pub start: String,
    pub sequence_terminator: Option<String>,
    pub rules: Vec<RuleInput>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuleInput {
    pub name: String,
    pub decl_order: u32,
    pub prec: i32,
    pub left_recursive: bool,
    pub rhs: Pattern,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Pattern {
    Seq {
        items: Vec<PatternItem>,
    },
    Choice {
        alts: Vec<Pattern>,
    },
    Token {
        lit: String,
    },
    Ref {
        name: String,
    },
    NegPred {
        inner: Box<Pattern>,
    },
    Atomic {
        inner: Box<Pattern>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PatternItem {
    Pattern { value: Pattern },
    Terminator { lit: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenInput {
    pub grammar_id: String,
    pub tokens: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClimbRow {
    pub rule: String,
    pub prec: i32,
    pub rank: u32,
    pub left_recursive: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrammarRow {
    pub grammar_id: String,
    pub start: String,
    pub sequence_terminator: Option<String>,
    pub rules: Vec<RuleInput>,
    pub source: String,
    pub ingest_order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphFile {
    pub ingest_seq: u32,
    pub grammars: Vec<GrammarRow>,
    pub climb_table: Vec<ClimbRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpanNode {
    pub kind: String,
    pub value: Option<String>,
    pub span: [usize; 2],
    pub recovered: bool,
    pub children: Vec<SpanNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParseTreeFile {
    pub grammar_id: String,
    pub root: SpanNode,
    pub recovered_nodes: Vec<SpanNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpanLedgerRow {
    pub kind: String,
    pub span: [usize; 2],
    pub recovered: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditFile {
    pub grammar_id: String,
    pub ingest_seq: u32,
    pub spans: Vec<SpanLedgerRow>,
}

#[derive(Debug, Clone)]
pub struct OpInfo {
    pub token: String,
    pub prec: i32,
    pub assoc_left: bool,
}
