pub mod score;
pub mod tiebreak;

use std::collections::BTreeMap;

use ts_tokenize::token_dedupe::index_terms;

use ts_fuzzy::typo_expand::expand_token;
use ts_types::document::Document;
use ts_types::search::SearchHit;

use crate::score::token_match_weight;

pub fn rank_documents(
    docs: &[Document],
    query_tokens: &[String],
    expanded: &[Vec<String>],
    _vocabulary: &[String],
) -> Vec<SearchHit> {
    let mut hits = Vec::new();
    for doc in docs {
        let doc_terms = index_terms(&doc.searchable_text());
        let mut score = 0.0;
        for (qi, qtok) in query_tokens.iter().enumerate() {
            let variants = &expanded[qi];
            let mut best = 0.0;
            for dt in &doc_terms {
                for variant in variants {
                    let typo = variant != qtok;
                    let w = token_match_weight(variant, dt, typo);
                    if w > best {
                        best = w;
                    }
                }
                if best >= 1.0 {
                    break;
                }
            }
            if best <= 0.0 {
                score = 0.0;
                break;
            }
            score += best;
        }
        if score > 0.0 {
            hits.push(SearchHit {
                docid: doc.docid.clone(),
                score,
            });
        }
    }
    tiebreak::apply_tiebreak(&mut hits, docs);
    hits
}

pub fn build_vocabulary(index: &BTreeMap<String, Vec<String>>) -> Vec<String> {
    index.keys().cloned().collect()
}

pub fn expand_query(query_tokens: &[String], vocabulary: &[String]) -> Vec<Vec<String>> {
    query_tokens
        .iter()
        .map(|t| expand_token(t, vocabulary))
        .collect()
}
