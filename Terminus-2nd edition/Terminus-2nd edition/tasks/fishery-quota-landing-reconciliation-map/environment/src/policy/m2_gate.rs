pub fn permit_covers_landing(landed_at: &str, valid_from: &str, valid_until: &str) -> bool {
    let landed = &landed_at[..10.min(landed_at.len())];
    landed >= valid_from && landed < valid_until
}

pub fn species_on_permit(species: &str, allowed: &[String]) -> bool {
    allowed.iter().any(|s| s.eq_ignore_ascii_case(species))
}
