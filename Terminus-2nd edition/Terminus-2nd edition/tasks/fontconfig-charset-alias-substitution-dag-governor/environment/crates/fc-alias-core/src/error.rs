use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FcError {
    Io(String),
    Parse(String),
    UnknownCharset(String),
    UnknownAlias(String),
    CycleDetected,
    StagingMissing,
}

pub type Result<T> = std::result::Result<T, FcError>;

impl fmt::Display for FcError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FcError::Io(msg) => write!(f, "io: {msg}"),
            FcError::Parse(msg) => write!(f, "parse: {msg}"),
            FcError::UnknownCharset(name) => write!(f, "unknown charset {name}"),
            FcError::UnknownAlias(name) => write!(f, "unknown alias {name}"),
            FcError::CycleDetected => write!(f, "alias cycle detected"),
            FcError::StagingMissing => write!(f, "compiled staging missing; run ingest first"),
        }
    }
}

impl std::error::Error for FcError {}
