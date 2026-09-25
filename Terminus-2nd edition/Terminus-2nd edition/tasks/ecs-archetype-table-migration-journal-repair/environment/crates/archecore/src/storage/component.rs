use std::collections::BTreeMap;

use crate::model::ComponentId;

#[allow(unused_variables)]
pub fn registration_order(names: &[String], seed: &str) -> Vec<String> {
    let mut sorted = names.to_vec();
    sorted.sort();
    sorted
}

pub fn build_component_map(order: &[String]) -> BTreeMap<String, ComponentId> {
    order
        .iter()
        .enumerate()
        .map(|(idx, name)| (name.clone(), idx as ComponentId))
        .collect()
}
