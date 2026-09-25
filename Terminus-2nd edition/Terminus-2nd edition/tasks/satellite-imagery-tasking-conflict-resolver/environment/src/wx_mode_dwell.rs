use crate::tasking_types::SensorModeSpec;
use std::collections::BTreeMap;

pub fn setup_duration(
    modes: &BTreeMap<String, SensorModeSpec>,
    mode: &str,
    _warm: bool,
) -> u64 {
    modes.get(mode).map(|m| m.cold_setup_sec).unwrap_or(0)
}
