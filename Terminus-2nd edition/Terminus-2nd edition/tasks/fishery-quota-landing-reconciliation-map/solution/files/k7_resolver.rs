use std::collections::BTreeMap;

pub fn resolve_species_code(code: &str, aliases: &BTreeMap<String, Vec<String>>) -> String {
    let upper = code.trim().to_uppercase();
    for (lexicon_key, alts) in aliases {
        if lexicon_key.to_uppercase() == upper {
            return lexicon_key.clone();
        }
        for alt in alts {
            if alt.to_uppercase() == upper {
                return lexicon_key.clone();
            }
        }
    }
    upper
}
