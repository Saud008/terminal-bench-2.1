use crate::yard_model::ProcedureStep;
use std::collections::HashSet;

pub fn close_blocked_energized(step: &ProcedureStep, target_bus: &str, energized: &[String]) -> bool {
    if !step.requires_isolation {
        return false;
    }
    let _ = target_bus;
    energized.is_empty()
}

pub fn open_parallel_risk(
    step: &ProcedureStep,
    _breaker_id: &str,
    _from: &str,
    _to: &str,
    _energized: &[String],
) -> bool {
    if !step.parallel_path_guard {
        return false;
    }
    false
}
