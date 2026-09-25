use std::collections::BTreeMap;

use query_planner::parse::parse_query;
use ts_facet::counter::facet_brand_counts;
use ts_filter::brand_filter::brand_matches;
use ts_fuzzy::typo_expand::expand_token;
use ts_ranker::{build_vocabulary, rank_documents};
use ts_types::index::IndexFile;
use ts_types::search::SearchResult;

pub fn run_search(index: &IndexFile, query: &str, brand_filter: Option<&str>) -> Result<SearchResult, String> {
    let query_tokens = parse_query(query)?;
    let full_vocab = build_vocabulary(&index.token_index);
    let expanded = query_tokens
        .iter()
        .map(|t| expand_token(t, &full_vocab))
        .collect::<Vec<_>>();
    let mut hits = rank_documents(
        &index.documents,
        &query_tokens,
        &expanded,
        &full_vocab,
    );
    if let Some(brand) = brand_filter {
        hits.retain(|hit| {
            index
                .documents
                .iter()
                .any(|doc| doc.docid == hit.docid && brand_matches(doc, brand))
        });
    }
    let facets = BTreeMap::from([(
        "brand".to_string(),
        facet_brand_counts(&index.documents, &hits),
    )]);
    Ok(SearchResult {
        hits,
        facets,
        query: query.to_string(),
        filter_brand: brand_filter.map(|s| s.to_string()),
    })
}
