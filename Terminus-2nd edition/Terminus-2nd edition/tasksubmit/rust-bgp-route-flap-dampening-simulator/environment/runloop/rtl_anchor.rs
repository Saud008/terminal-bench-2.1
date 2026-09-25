use crate::route_model::PrefixLedger;

pub fn forecast_anchor_ms(slot: &PrefixLedger, peer_max_ts: u64) -> u64 {
    peer_max_ts.max(slot.last_ts_ms)
}
