use crate::model::{SimState, WireFrame};
use crate::sim::state::apply_input;

pub fn apply_frame_inputs(state: &mut SimState, frame: &WireFrame) {
    if frame.inputs.is_empty() {
        return;
    }
    for inp in &frame.inputs {
        let tick = u64::from(frame.base_tick) + u64::from(inp.tick_offset);
        apply_input(state, tick, inp.opcode, inp.value);
    }
}
