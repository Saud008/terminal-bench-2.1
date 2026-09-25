use crate::yard_model::{LockoutRow, ProcedureStep};

pub fn is_locked(lockouts: &[LockoutRow], step: &ProcedureStep, from_bus: &str, to_bus: &str) -> bool {
    for lot in lockouts {
        if !lot.active {
            continue;
        }
        for eq in &lot.equipment_ids {
            if eq == &step.breaker_id || eq == from_bus || eq == to_bus {
                return true;
            }
        }
    }
    false
}
