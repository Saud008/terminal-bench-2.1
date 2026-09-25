use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LimitKind {
    Depth,
    Bytes,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecodeError {
    LimitExceeded { kind: LimitKind },
    InvalidVarint,
    InvalidTag(u8),
    UnexpectedEof,
}

impl DecodeError {
    pub fn code(&self) -> &'static str {
        match self {
            DecodeError::LimitExceeded { .. } => "limit_exceeded",
            DecodeError::InvalidVarint => "invalid_varint",
            DecodeError::InvalidTag(_) => "invalid_tag",
            DecodeError::UnexpectedEof => "unexpected_eof",
        }
    }

    pub fn limit_kind(&self) -> Option<LimitKind> {
        match self {
            DecodeError::LimitExceeded { kind } => Some(*kind),
            _ => None,
        }
    }

    pub fn into_report_error(self) -> DecodeError {
        match self {
            DecodeError::LimitExceeded { .. } => DecodeError::UnexpectedEof,
            other => other,
        }
    }
}
