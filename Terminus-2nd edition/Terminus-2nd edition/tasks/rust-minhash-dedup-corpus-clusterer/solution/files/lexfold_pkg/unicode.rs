use unicode_normalization::UnicodeNormalization;

pub fn normalize_unicode(raw: &str) -> String {
    raw.nfkc().collect::<String>().to_lowercase()
}
