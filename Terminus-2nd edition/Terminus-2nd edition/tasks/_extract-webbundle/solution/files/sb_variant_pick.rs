use crate::wble_reader::ExchangeRecord;
use crate::url_norm::canonical_url;

pub fn resolve_duplicates(exchanges: Vec<ExchangeRecord>) -> Vec<ExchangeRecord> {
    let mut best: std::collections::HashMap<String, ExchangeRecord> = std::collections::HashMap::new();
    for ex in exchanges {
        let key = canonical_url(&ex.url);
        best.entry(key)
            .and_modify(|cur| {
                if ex.variant_id > cur.variant_id {
                    *cur = ex.clone();
                }
            })
            .or_insert(ex);
    }
    let mut out: Vec<ExchangeRecord> = best.into_values().collect();
    out.sort_by(|a, b| canonical_url(&a.url).cmp(&canonical_url(&b.url)));
    out
}
