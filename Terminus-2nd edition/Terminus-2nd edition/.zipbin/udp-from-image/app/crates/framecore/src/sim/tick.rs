use std::collections::BTreeSet;

use crate::model::{SimState, WireFrame};
use crate::sim::state::apply_input;

pub fn apply_frame_inputs(state: &mut SimState, frame: &WireFrame) {
    if frame.inputs.is_empty() {
        return;
    }
    let offsets: BTreeSet<u16> = frame.inputs.iter().map(|i| i.tick_offset).collect();
    let max_off = *offsets.iter().max().unwrap();
    if offsets.len() as u16 != max_off + 1 {
        return;
    }
    for inp in &frame.inputs {
        let tick = u64::from(frame.base_tick) + u64::from(inp.tick_offset);
        apply_input(state, tick, inp.opcode, inp.value);
    }
}
