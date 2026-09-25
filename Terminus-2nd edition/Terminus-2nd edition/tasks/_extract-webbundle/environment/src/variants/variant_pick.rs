use crate::wble_reader::ExchangeRecord;
use crate::url_norm::canonical_url;

pub fn resolve_duplicates(exchanges: Vec<ExchangeRecord>) -> Vec<ExchangeRecord> {
    let mut seen: std::collections::HashMap<String, ExchangeRecord> = std::collections::HashMap::new();
    for ex in exchanges {
        let key = canonical_url(&ex.url);
        seen.entry(key).or_insert(ex);
    }
    let mut out: Vec<ExchangeRecord> = seen.into_values().collect();
    out.sort_by(|a, b| canonical_url(&a.url).cmp(&canonical_url(&b.url)));
    out
}
