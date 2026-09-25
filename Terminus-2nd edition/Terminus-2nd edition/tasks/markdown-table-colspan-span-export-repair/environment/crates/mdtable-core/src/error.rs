use thiserror::Error;

#[derive(Debug, Error)]
pub enum TableError {
    #[error("no pipe table found in {0}")]
    NoTable(String),
    #[error("invalid span marker in cell: {0}")]
    InvalidMarker(String),
}
