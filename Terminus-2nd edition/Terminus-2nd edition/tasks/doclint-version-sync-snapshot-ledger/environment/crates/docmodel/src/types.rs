use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Range {
    pub start: Position,
    pub end: Position,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Position {
    pub line: u32,
    pub character: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContentChange {
    pub range: Option<Range>,
    pub text: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StagedEdit {
    pub range: Range,
    pub text: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Document {
    pub uri: String,
    pub version: i32,
    pub text: String,
    pub staging: Vec<StagedEdit>,
    pub last_change_version: Option<i32>,
}

impl Document {
    pub fn new(uri: String, text: String) -> Self {
        Self {
            uri,
            version: 0,
            text,
            staging: Vec::new(),
            last_change_version: None,
        }
    }
}
