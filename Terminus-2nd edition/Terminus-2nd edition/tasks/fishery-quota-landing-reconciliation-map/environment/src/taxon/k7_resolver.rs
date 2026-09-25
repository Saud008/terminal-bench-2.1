use std::collections::BTreeMap;

pub fn resolve_species_code(code: &str, aliases: &BTreeMap<String, Vec<String>>) -> String {
    code.trim().to_uppercase()
}
