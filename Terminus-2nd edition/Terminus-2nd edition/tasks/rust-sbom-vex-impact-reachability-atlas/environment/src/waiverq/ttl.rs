use chrono::{DateTime, Utc};

use crate::types::StageVex;

pub fn is_active(stmt: &StageVex) -> bool {
    match &stmt.expires_at {
        None => true,
        Some(exp) => {
            let Ok(expiry) = DateTime::parse_from_rfc3339(exp) else {
                return false;
            };
            let now = Utc::now();
            now <= expiry.with_timezone(&Utc)
        }
    }
}

pub fn filter_active<'a>(statements: &'a [StageVex]) -> Vec<&'a StageVex> {
    statements.iter().filter(|s| is_active(s)).collect()
}
