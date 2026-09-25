use ts_types::document::Document;
use ts_types::search::SearchHit;

pub fn apply_tiebreak(hits: &mut [SearchHit], docs: &[Document]) {
    let order_map: std::collections::HashMap<String, u64> = docs
        .iter()
        .map(|d| (d.docid.clone(), d.insertion_order))
        .collect();
    hits.sort_by(|a, b| {
        let score_cmp = b
            .score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal);
        if (a.score - b.score).abs() > 1e-9 {
            return score_cmp;
        }
        let ao = order_map.get(&a.docid).copied().unwrap_or(0);
        let bo = order_map.get(&b.docid).copied().unwrap_or(0);
        ao.cmp(&bo)
    });
}
