use ts_types::document::Document;
use ts_types::search::SearchHit;

pub fn apply_tiebreak(hits: &mut [SearchHit], _docs: &[Document]) {
    hits.sort_by(|a, b| {
        let score_cmp = b
            .score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal);
        if (a.score - b.score).abs() > 1e-9 {
            return score_cmp;
        }
        a.docid.cmp(&b.docid)
    });
}
