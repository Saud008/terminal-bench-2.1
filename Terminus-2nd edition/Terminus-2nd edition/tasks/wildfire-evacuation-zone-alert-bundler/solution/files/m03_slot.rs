use crate::hazard_schema::ShelterSpec;
use std::collections::BTreeMap;

pub fn assign_shelter(
    shelters: &[ShelterSpec],
    shelter_id: &str,
    evacuees: u32,
    remaining: &mut BTreeMap<String, u32>,
) -> bool {
    let cap = shelters
        .iter()
        .find(|s| s.shelter_id == shelter_id)
        .map(|s| s.capacity)
        .unwrap_or(0);
    let left = remaining.get(shelter_id).copied().unwrap_or(cap);
    if evacuees <= left {
        remaining.insert(shelter_id.to_string(), left - evacuees);
        true
    } else {
        false
    }
}

pub fn init_remaining(shelters: &[ShelterSpec]) -> BTreeMap<String, u32> {
    shelters
        .iter()
        .map(|s| (s.shelter_id.clone(), s.capacity))
        .collect()
}
