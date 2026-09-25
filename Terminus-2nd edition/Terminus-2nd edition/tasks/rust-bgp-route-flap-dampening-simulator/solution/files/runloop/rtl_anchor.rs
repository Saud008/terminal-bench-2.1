use crate::route_model::PrefixLedger;

pub fn forecast_anchor_ms(slot: &PrefixLedger, _peer_max_ts: u64) -> u64 {
    slot.last_ts_ms
}
