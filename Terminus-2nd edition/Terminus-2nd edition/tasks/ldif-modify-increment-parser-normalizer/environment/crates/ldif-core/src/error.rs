use std::fmt;

#[derive(Debug)]
pub enum LdifError {
    Io(String),
    Parse(String),
    Apply(String),
    Audit(String),
}

impl fmt::Display for LdifError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LdifError::Io(msg) => write!(f, "io: {msg}"),
            LdifError::Parse(msg) => write!(f, "parse: {msg}"),
            LdifError::Apply(msg) => write!(f, "apply: {msg}"),
            LdifError::Audit(msg) => write!(f, "audit: {msg}"),
        }
    }
}

impl std::error::Error for LdifError {}

pub type Result<T> = std::result::Result<T, LdifError>;
