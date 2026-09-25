pub fn deadline_ok(start_slot: u32, duration_slots: u32, deadline_slot: u32) -> bool {
    start_slot + duration_slots - 1 <= deadline_slot
}
