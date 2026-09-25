use crate::types::RouteRow;

pub fn classify_row(row: &RouteRow) -> String {
    if row.outage_suppressed {
        return "OUTAGE_SUPPRESSED".to_string();
    }
    if !row.connection_ok {
        return "CONNECTION_INFEASIBLE".to_string();
    }
    if row.target_flight_id.is_empty() {
        return "BELT_UNMAPPED".to_string();
    }
    "ROUTED_OK".to_string()
}

fn cause_rank(c: &str) -> u8 {
    match c {
        "OUTAGE_SUPPRESSED" => 0,
        "BELT_UNMAPPED" => 1,
        "CONNECTION_INFEASIBLE" => 2,
        "ROUTED_OK" => 3,
        _ => 9,
    }
}

pub fn pick_dominant_cause(existing: &str, incoming: &str) -> String {
    if cause_rank(incoming) < cause_rank(existing) {
        incoming.to_string()
    } else {
        existing.to_string()
    }
}
