use crate::tasking_types::SensorModeSpec;
use std::collections::BTreeMap;

pub fn setup_duration(
    modes: &BTreeMap<String, SensorModeSpec>,
    mode: &str,
    warm: bool,
) -> u64 {
    let spec = modes.get(mode).unwrap();
    if warm { spec.warm_setup_sec } else { spec.cold_setup_sec }
}
