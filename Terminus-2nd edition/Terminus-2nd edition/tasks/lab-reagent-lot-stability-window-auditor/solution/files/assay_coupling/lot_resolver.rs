use crate::win_schema::{LotRecord, TelemetryRow};

fn alias_eq(a: &str, b: &str) -> bool {
    a.eq_ignore_ascii_case(b)
}

pub fn resolve_lot_id(alias: &str, lots: &[LotRecord]) -> Option<String> {
    for lot in lots {
        if alias_eq(&lot.lot_id, alias) {
            return Some(lot.lot_id.clone());
        }
        for a in &lot.aliases {
            if alias_eq(a, alias) {
                return Some(lot.lot_id.clone());
            }
        }
    }
    None
}

pub fn telemetry_for_lot(lot_id: &str, rows: &[TelemetryRow], lots: &[LotRecord]) -> Vec<TelemetryRow> {
    rows.iter()
        .filter(|row| resolve_lot_id(&row.lot_alias, lots).as_deref() == Some(lot_id))
        .cloned()
        .collect()
}
