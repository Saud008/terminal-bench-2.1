use std::fmt::{Display, Formatter};

#[derive(Debug)]
pub enum FitError {
    Io(String),
    Parse(String),
    CrcMismatch { expected: u16, actual: u16 },
    StagingMissing(String),
    StagingMismatch(String),
}

impl Display for FitError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(msg) => write!(f, "io error: {msg}"),
            Self::Parse(msg) => write!(f, "parse error: {msg}"),
            Self::CrcMismatch { expected, actual } => {
                write!(f, "crc mismatch expected={expected} actual={actual}")
            }
            Self::StagingMissing(msg) => write!(f, "staging missing: {msg}"),
            Self::StagingMismatch(msg) => write!(f, "staging mismatch: {msg}"),
        }
    }
}

impl std::error::Error for FitError {}

impl From<std::io::Error> for FitError {
    fn from(value: std::io::Error) -> Self {
        Self::Io(value.to_string())
    }
}

impl From<serde_json::Error> for FitError {
    fn from(value: serde_json::Error) -> Self {
        Self::Parse(value.to_string())
    }
}
