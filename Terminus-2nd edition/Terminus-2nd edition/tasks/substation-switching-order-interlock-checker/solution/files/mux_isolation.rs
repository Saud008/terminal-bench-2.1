use crate::energize_propagate;
use crate::yard_model::{BreakerStates, ProcedureStep};

pub fn close_blocked_energized(step: &ProcedureStep, target_bus: &str, energized: &[String]) -> bool {
    if !step.requires_isolation {
        return false;
    }
    energized.iter().any(|b| b == target_bus)
}

pub fn open_parallel_risk(
    step: &ProcedureStep,
    breaker_id: &str,
    from: &str,
    to: &str,
    sources: &[String],
    triples: &[(String, String, String)],
    states: &BreakerStates,
) -> bool {
    if !step.parallel_path_guard {
        return false;
    }
    let before: std::collections::HashSet<String> = energize_propagate::compute_energized(sources, triples, states)
        .into_iter()
        .collect();
    let mut sim = states.clone();
    sim.insert(breaker_id.to_string(), "open".into());
    let after: std::collections::HashSet<String> = energize_propagate::compute_energized(sources, triples, &sim)
        .into_iter()
        .collect();
    let frm_live = before.contains(from);
    let to_live = before.contains(to);
    let frm_after = after.contains(from);
    let to_after = after.contains(to);
    frm_live && to_live && (frm_after != to_live || to_after != frm_live)
}
