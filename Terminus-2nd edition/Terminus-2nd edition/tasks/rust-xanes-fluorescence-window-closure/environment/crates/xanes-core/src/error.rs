use thiserror::Error;

pub type Result<T> = std::result::Result<T, XanesError>;

#[derive(Debug, Error)]
pub enum XanesError {
    #[error("undeclared edge_code: {0}")]
    UndeclaredEdge(String),
    #[error("unknown edge_code: {0}")]
    UnknownEdge(String),
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
    #[error("json: {0}")]
    Json(#[from] serde_json::Error),
    #[error("{0}")]
    Msg(String),
}
