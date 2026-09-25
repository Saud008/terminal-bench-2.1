use std::fmt;

#[derive(Debug)]
pub enum DecodeError {
    Io(String),
    Format(String),
    Checksum(String),
}

impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DecodeError::Io(msg) => write!(f, "io: {msg}"),
            DecodeError::Format(msg) => write!(f, "format: {msg}"),
            DecodeError::Checksum(msg) => write!(f, "checksum: {msg}"),
        }
    }
}

impl std::error::Error for DecodeError {}
