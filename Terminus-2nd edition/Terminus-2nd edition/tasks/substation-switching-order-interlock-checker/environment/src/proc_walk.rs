use crate::breaker_table;
use crate::energize_propagate;
use crate::mux_isolation;
use crate::loto_enforce;
use crate::procedure_steps;
use crate::unsafe_explain;
use crate::yard_model::{
    BreakerStates, ProcedureStep, ScenarioFile, StepResult, YardSnapshot,
};

pub fn simulate_procedure(snap: &YardSnapshot, sf: &ScenarioFile) -> Vec<StepResult> {
    let breaker_triples: Vec<(String, String, String)> = snap
        .breakers
        .iter()
        .map(|b| (b.breaker_id.clone(), b.from_bus.clone(), b.to_bus.clone()))
        .collect();
    let steps = procedure_steps::sorted_steps(sf);
    let mut results = Vec::new();
    for step in steps {
        let mut states = breaker_table::initial_states(&snap.breakers);
        let energized = energize_propagate::compute_energized(
            &snap.energized_sources,
            &breaker_triples,
            &states,
        );
        let row = evaluate_one(&snap, sf, &mut states, &breaker_triples, &energized, &step);
        results.push(row);
    }
    results
}

fn evaluate_one(
    _snap: &YardSnapshot,
    sf: &ScenarioFile,
    states: &mut BreakerStates,
    triples: &[(String, String, String)],
    energized: &[String],
    step: &ProcedureStep,
) -> StepResult {
    let mut reasons = Vec::new();
    if step.step_index != procedure_steps::expected_index(step.step_index) {
        reasons.push("out_of_order".into());
    }
    let mut target_bus = String::new();
    let mut found = false;
    for (id, from, to) in triples {
        if id == &step.breaker_id {
            target_bus = to.clone();
            found = true;
            break;
        }
    }
    if !found {
        reasons.push("unknown_breaker".into());
    }
    if loto_enforce::is_locked(&sf.lockouts, step) {
        reasons.push("lockout_active".into());
    }
    if mux_isolation::close_blocked_energized(step, &target_bus, energized) {
        reasons.push("close_blocked_energized".into());
    }
    if mux_isolation::open_parallel_risk(step, &step.breaker_id, "", "", energized) {
        reasons.push("open_parallel_risk".into());
    }
    let safe = reasons.is_empty();
    if safe {
        breaker_table::apply_action(states, &step.breaker_id, &step.action);
    }
    let post = energize_propagate::compute_energized(&sf.energized_sources, triples, states);
    StepResult {
        step_index: step.step_index,
        action: step.action.clone(),
        breaker_id: step.breaker_id.clone(),
        safe,
        reason_codes: unsafe_explain::normalize_codes(reasons),
        energized_buses: post,
    }
}
