use crate::types::{StageVex, STATUS_AFFECTED, STATUS_FIXED, STATUS_NOT_AFFECTED, STATUS_UNDER, STATUS_UNKNOWN};

pub fn status_rank(status: &str) -> i32 {
    match status {
        STATUS_FIXED => 4,
        STATUS_NOT_AFFECTED => 3,
        STATUS_UNDER => 2,
        STATUS_AFFECTED => 1,
        _ => 0,
    }
}

pub fn pick_effective<'a>(statements: &'a [StageVex]) -> Option<&'a StageVex> {
    statements
        .iter()
        .max_by(|a, b| {
            status_rank(&a.status)
                .cmp(&status_rank(&b.status))
                .then_with(|| a.updated_at.cmp(&b.updated_at))
        })
}

pub fn effective_status(statements: &[StageVex]) -> String {
    pick_effective(statements)
        .map(|s| s.status.clone())
        .unwrap_or_else(|| STATUS_UNKNOWN.to_string())
}
