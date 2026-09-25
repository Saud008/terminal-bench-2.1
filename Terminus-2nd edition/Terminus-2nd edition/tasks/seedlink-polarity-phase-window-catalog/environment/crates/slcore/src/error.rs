use std::fmt;

#[derive(Debug)]
pub enum SlError {
    Io(String),
    Parse(String),
    StagingMissing(String),
    StagingMismatch(String),
}

impl fmt::Display for SlError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SlError::Io(msg) => write!(f, "io error: {msg}"),
            SlError::Parse(msg) => write!(f, "parse error: {msg}"),
            SlError::StagingMissing(msg) => write!(f, "staging missing: {msg}"),
            SlError::StagingMismatch(msg) => write!(f, "staging mismatch: {msg}"),
        }
    }
}

impl std::error::Error for SlError {}

impl From<std::io::Error> for SlError {
    fn from(value: std::io::Error) -> Self {
        SlError::Io(value.to_string())
    }
}

impl From<serde_json::Error> for SlError {
    fn from(value: serde_json::Error) -> Self {
        SlError::Parse(value.to_string())
    }
}
