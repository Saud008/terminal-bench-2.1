use crate::types::{BeltSpec, HubLatch, ScanRow};

pub fn pick_belt(hub: &HubLatch, row: &ScanRow) -> Option<BeltSpec> {
    let mut candidates: Vec<&BeltSpec> = hub
        .belts
        .iter()
        .filter(|b| b.belt_id == row.belt_id && b.station_code == row.station_code)
        .collect();
    if candidates.is_empty() {
        return None;
    }
    candidates.sort_by_key(|b| b.belt_id.clone());
    candidates.first().cloned().cloned()
}
