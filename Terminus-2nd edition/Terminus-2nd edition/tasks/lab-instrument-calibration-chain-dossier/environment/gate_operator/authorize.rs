use crate::chain_schema::Technician;

pub fn technician_authorized(tech: &Technician, _instrument_id: &str, as_of: &str) -> bool {
    tech.qual_expires.as_str() >= as_of
}
