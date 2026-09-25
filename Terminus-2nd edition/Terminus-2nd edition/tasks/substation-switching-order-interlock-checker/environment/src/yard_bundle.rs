use crate::yard_model::ScenarioFile;

pub fn touch_bundle(sf: &ScenarioFile) -> usize {
    sf.breakers.len() + sf.buses.len()
}
