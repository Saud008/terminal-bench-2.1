use crate::tasking_types::{ImagingRequest, PriorityContract};
use std::collections::BTreeMap;

pub fn contract_rank(contracts: &BTreeMap<String, PriorityContract>, contract_id: &str) -> u32 {
    contracts.get(contract_id).map(|c| c.preempt_rank).unwrap_or(0)
}

pub fn sort_requests(
    requests: &mut [ImagingRequest],
    contracts: &BTreeMap<String, PriorityContract>,
) {
    requests.sort_by(|a, b| {
        let ra = contract_rank(contracts, &a.contract_id);
        let rb = contract_rank(contracts, &b.contract_id);
        ra.cmp(&rb).then_with(|| a.request_id.cmp(&b.request_id))
    });
}

pub fn should_preempt(winner: u32, loser: u32) -> bool {
    winner >= loser
}
