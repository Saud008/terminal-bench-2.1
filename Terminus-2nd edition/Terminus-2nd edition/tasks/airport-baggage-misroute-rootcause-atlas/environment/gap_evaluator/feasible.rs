use crate::types::{ConnectionSpec, FlightSpec, HubLatch};

pub fn connection_feasible(hub: &HubLatch, inbound: &str, outbound: &str) -> bool {
    let flights: std::collections::BTreeMap<String, &FlightSpec> = hub
        .flights
        .iter()
        .map(|f| (f.flight_id.clone(), f))
        .collect();
    let inbound_f = match flights.get(inbound) {
        Some(v) => *v,
        None => return false,
    };
    let outbound_f = match flights.get(outbound) {
        Some(v) => *v,
        None => return false,
    };
    let rule = hub.connections.iter().find(|c| {
        c.inbound_flight == inbound && c.outbound_flight == outbound
    });
    let min_mct = crate::mct_override().or_else(|| rule.map(|r| r.min_connect_minutes)).unwrap_or(0);
    let gap = outbound_f.dep_minute.saturating_sub(inbound_f.arr_minute);
    gap > min_mct
}

pub fn find_connection<'a>(hub: &'a HubLatch, target_flight: &str) -> Option<&'a ConnectionSpec> {
    hub.connections
        .iter()
        .find(|c| c.outbound_flight == target_flight)
}
