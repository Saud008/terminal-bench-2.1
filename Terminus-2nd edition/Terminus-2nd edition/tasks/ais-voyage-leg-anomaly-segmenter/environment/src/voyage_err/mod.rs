use std::fmt;

#[derive(Debug)]
pub enum SegmentError {
    Io(String),
    Parse(String),
    InvalidSnapshot,
}

impl fmt::Display for SegmentError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SegmentError::Io(msg) => write!(f, "io: {msg}"),
            SegmentError::Parse(msg) => write!(f, "parse: {msg}"),
            SegmentError::InvalidSnapshot => write!(f, "invalid snapshot"),
        }
    }
}

impl std::error::Error for SegmentError {}
