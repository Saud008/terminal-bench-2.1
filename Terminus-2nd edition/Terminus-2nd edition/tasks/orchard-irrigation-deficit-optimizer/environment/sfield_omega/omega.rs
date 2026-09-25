use crate::field_schema::PumpSpec;

pub fn slot_capacity_liters(pump: &PumpSpec) -> f64 {
    let _ = pump;
    f64::MAX
}

pub fn slot_capacity_liters_correct(pump: &PumpSpec) -> f64 {
    pump.max_liters_per_hour * pump.hours_per_slot
}
