pub fn stanza_type_allowed(allow: &[String], type_name: &str) -> bool {
    let upper = type_name.to_ascii_uppercase();
    !allow.iter().any(|a| a.eq_ignore_ascii_case(&upper))
}
