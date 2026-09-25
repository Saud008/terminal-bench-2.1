use unicode_normalization::UnicodeNormalization;

pub fn normalize_unicode(raw: &str) -> String {
    raw.nfc().collect::<String>().to_lowercase()
}
