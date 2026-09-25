use std::fmt;

#[derive(Debug)]
pub enum AuditError {
    Io(String),
    Cbor(String),
    Parse(String),
    Ledger(String),
    EmptyLedger,
}

impl fmt::Display for AuditError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AuditError::Io(s) => write!(f, "io: {s}"),
            AuditError::Cbor(s) => write!(f, "cbor: {s}"),
            AuditError::Parse(s) => write!(f, "parse: {s}"),
            AuditError::Ledger(s) => write!(f, "ledger: {s}"),
            AuditError::EmptyLedger => write!(f, "ledger empty"),
        }
    }
}

impl std::error::Error for AuditError {}
