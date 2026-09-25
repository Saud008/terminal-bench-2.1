use crate::yard_model::{LockoutRow, ProcedureStep};

pub fn is_locked(lockouts: &[LockoutRow], step: &ProcedureStep) -> bool {
    for lot in lockouts {
        if !lot.active {
            continue;
        }
        for eq in &lot.equipment_ids {
            if eq == &step.breaker_id {
                if step.action == "close" {
                    return true;
                }
            }
        }
    }
    false
}
