use lab_calibration_chain::chain_schema::Technician;

pub fn technician_authorized(tech: &Technician, instrument_id: &str, as_of: &str) -> bool {
    if tech.qual_expires.as_str() < as_of {
        return false;
    }
    tech.scope_instruments.iter().any(|s| s == instrument_id)
}
