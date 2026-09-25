use crate::types::{HubLatch, OutageSpec};

pub fn scan_suppressed(hub: &HubLatch, station: &str, minute: u64) -> bool {
    if let Some(st) = crate::outage_station_override() {
        if st != station {
            return false;
        }
    }
    hub.outages.iter().any(|o| outage_covers(o, station, minute))
}

fn outage_covers(o: &OutageSpec, station: &str, minute: u64) -> bool {
    if o.station_code != station {
        return false;
    }
    minute >= o.start_minute && minute <= o.end_minute
}
