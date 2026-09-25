use crate::yard_model::{ProcedureStep, ScenarioFile};

pub fn sorted_steps(sf: &ScenarioFile) -> Vec<ProcedureStep> {
    let mut steps = sf.procedure.clone();
    steps.sort_by_key(|s| s.step_index);
    steps
}

pub fn expected_index(seq: u32) -> u32 {
    seq
}
