/// Allow-list: type is permitted when its ASCII-uppercase form equals an allow entry
/// compared case-insensitively.
pub fn stanza_type_allowed(allow: &[String], type_name: &str) -> bool {
    allow
        .iter()
        .any(|a| a.eq_ignore_ascii_case(&type_name.to_ascii_uppercase()))
}
