use thiserror::Error;

#[derive(Debug, Error)]
pub enum CombatError {
    #[error("{0}")]
    InvalidRoster(String),
    #[error("{0}")]
    Io(#[from] std::io::Error),
    #[error("{0}")]
    Json(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, CombatError>;
