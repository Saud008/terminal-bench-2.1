use std::fmt;

#[derive(Debug)]
pub enum MavError {
    Parse(String),
    Validate(String),
    Session(String),
    Dedup(String),
    Checkpoint(String),
    Route(String),
    Publish(String),
}

pub type Result<T> = std::result::Result<T, MavError>;

impl fmt::Display for MavError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MavError::Parse(s) => write!(f, "parse error: {s}"),
            MavError::Validate(s) => write!(f, "validate error: {s}"),
            MavError::Session(s) => write!(f, "session error: {s}"),
            MavError::Dedup(s) => write!(f, "dedup error: {s}"),
            MavError::Checkpoint(s) => write!(f, "checkpoint error: {s}"),
            MavError::Route(s) => write!(f, "route error: {s}"),
            MavError::Publish(s) => write!(f, "publish error: {s}"),
        }
    }
}

impl std::error::Error for MavError {}
